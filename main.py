import streamlit as st
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# Configure Streamlit page
st.set_page_config(
    page_title="Art Intelligence Suite",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
ART_INSTITUTE_API = "https://api.artic.edu/api/v1/"
PLACEHOLDER_IMAGE = "https://via.placeholder.com/300x400.png?text=No+Image+Available"
ARTWORKS_PER_PAGE = 5  # Number of artworks to load per page

# Session State Initialization
if 'selected_artist' not in st.session_state:
    st.session_state.selected_artist = None
if 'selected_artwork' not in st.session_state:
    st.session_state.selected_artwork = None
if 'web_context' not in st.session_state:
    st.session_state.web_context = []
if 'artworks_list' not in st.session_state:
    st.session_state.artworks_list = []
if 'artworks_current_page' not in st.session_state:
    st.session_state.artworks_current_page = 1
if 'has_more_artworks' not in st.session_state:
    st.session_state.has_more_artworks = True


def get_artist_details(artist_id):
    """Get detailed artist information from API"""
    try:
        response = requests.get(
            f"{ART_INSTITUTE_API}artists/{artist_id}",
            params={'fields': 'id,title,birth_date,death_date,description'},
            timeout=10
        )
        response.raise_for_status()
        data = response.json().get('data', {})
        return {
            'id': data.get('id', artist_id),
            'title': data.get('title', 'Unknown Artist'),
            'birth_date': data.get('birth_date', 'Unknown'),
            'death_date': data.get('death_date', 'Unknown'),
            'description': data.get('description', 'No description available')
        }
    except requests.RequestException as e:
        st.error(f"Error fetching artist details: {str(e)}")
        return {'id': artist_id, 'title': 'Unknown Artist'}


def search_artists(query):
    """Search artists using API"""
    try:
        response = requests.get(
            f"{ART_INSTITUTE_API}artists/search",
            params={'q': query, 'limit': 10, 'fields': 'id,title'},
            timeout=10
        )
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.RequestException as e:
        st.error(f"Error searching artists: {str(e)}")
        return []


def get_random_artists():
    """Fetch random artist examples from API"""
    try:
        response = requests.get(
            f"{ART_INSTITUTE_API}artists",
            params={'limit': 5, 'fields': 'id,title'},
            timeout=5
        )
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.RequestException as e:
        st.error(f"Error fetching random artists: {str(e)}")
        return []


def get_artist_artworks(artist_id, page=1):
    """Get artworks for a specific artist with pagination"""
    try:
        response = requests.get(
            f"{ART_INSTITUTE_API}artworks/search",
            params={
                'query[term][artist_id]': artist_id,
                'limit': ARTWORKS_PER_PAGE,
                'page': page,
                'fields': 'id,title,image_id,date_display'
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return {
            'artworks': data.get('data', []),
            'pagination': data.get('pagination', {})
        }
    except requests.RequestException as e:
        st.error(f"Error fetching artist artworks: {str(e)}")
        return {'artworks': [], 'pagination': {}}


def get_artwork_details(artwork_id):
    """Get detailed artwork information from API"""
    try:
        response = requests.get(
            f"{ART_INSTITUTE_API}artworks/{artwork_id}",
            params={'fields': 'title,artist_title,date_display,medium_display,dimensions,image_id,style_titles'},
            timeout=10
        )
        response.raise_for_status()
        data = response.json().get('data', {})
        return {
            'id': data.get('id', artwork_id),
            'title': data.get('title', 'Untitled'),
            'artist_title': data.get('artist_title', 'Unknown'),
            'date_display': data.get('date_display', 'Unknown date'),
            'medium_display': data.get('medium_display', 'Unknown medium'),
            'dimensions': data.get('dimensions', 'N/A'),
            'image_id': data.get('image_id'),
            'style_titles': data.get('style_titles', [])
        }
    except requests.RequestException as e:
        st.error(f"Error fetching artwork details: {str(e)}")
        return {}


def web_research_artwork(artwork_title, artist_name):
    """Enhanced web research for artwork context"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    try:
        with DDGS() as ddgs:
            search_results = list(ddgs.text(
                f"{artwork_title} {artist_name} art historical context analysis",
                max_results=3
            ))

        context = []
        for result in search_results:
            try:
                page = requests.get(result['href'], timeout=10, headers=headers)
                soup = BeautifulSoup(page.content, 'html.parser')

                # Clean up page content
                for element in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe']):
                    element.decompose()

                content = soup.get_text(separator='\n', strip=True)
                context.append({
                    'source': result['href'],
                    'content': content[:1500]  # More conservative length limit
                })
            except Exception as e:
                continue
        return context
    except Exception as e:
        st.error(f"Error during web research: {str(e)}")
        return []


def display_artist_selection():
    """Main artist selection interface"""
    st.header("Artwork Context Explorer")

    example_artists = get_random_artists()
    if example_artists:
        st.markdown("**Example artists you could search:**")
        cols = st.columns(3)
        for idx, artist in enumerate(example_artists[:6]):
            with cols[idx % 3]:
                st.caption(f"▸ {artist.get('title', 'Unknown Artist')}")

    search_query = st.text_input("Search for an artist:", key="artist_search")

    if search_query:
        artists = search_artists(search_query)
        if artists:
            st.subheader("Matching Artists")
            cols = st.columns(3)
            for idx, artist in enumerate(artists):
                with cols[idx % 3]:
                    artist_id = artist.get('id', '')
                    if st.button(
                            artist.get('title', 'Unknown Artist'),
                            key=f"artist_{artist_id}_{idx}",
                            use_container_width=True
                    ):
                        full_details = get_artist_details(artist_id)
                        st.session_state.selected_artist = full_details
                        st.session_state.artworks_list = []
                        st.session_state.artworks_current_page = 1
                        st.session_state.has_more_artworks = True
                        st.rerun()
        else:
            st.warning("No artists found matching your query.")


def display_artwork_analysis():
    """Artwork selection interface with pagination"""
    if not st.session_state.selected_artist or 'id' not in st.session_state.selected_artist:
        st.error("Invalid artist selection")
        return

    artist_id = st.session_state.selected_artist['id']
    st.header(f"Artworks by {st.session_state.selected_artist.get('title', 'Unknown Artist')}")

    # Initial load of first page
    if not st.session_state.artworks_list and st.session_state.has_more_artworks:
        response = get_artist_artworks(artist_id, st.session_state.artworks_current_page)
        st.session_state.artworks_list = response.get('artworks', [])
        pagination = response.get('pagination', {})
        st.session_state.has_more_artworks = pagination.get('current_page', 1) < pagination.get('total_pages', 1)

    # Display artworks
    if st.session_state.artworks_list:
        cols = st.columns(3)
        for idx, artwork in enumerate(st.session_state.artworks_list):
            with cols[idx % 3]:
                image_id = artwork.get('image_id')
                st.image(
                    f"https://www.artic.edu/iiif/2/{image_id}/full/300,/0/default.jpg" if image_id else PLACEHOLDER_IMAGE,
                    use_container_width=True,
                    caption=artwork.get('title', 'Untitled')
                )

                if st.button(
                        "View Details",
                        key=f"artwork_{artwork.get('id', idx)}",
                        help="Click to view details",
                        use_container_width=True
                ):
                    st.session_state.selected_artwork = get_artwork_details(artwork.get('id', ''))
                    st.session_state.web_context = web_research_artwork(
                        st.session_state.selected_artwork['title'],
                        st.session_state.selected_artist['title']
                    )
                    st.rerun()

        # Load More button
        if st.session_state.has_more_artworks:
            if st.button("Load More Artworks", use_container_width=True):
                st.session_state.artworks_current_page += 1
                response = get_artist_artworks(artist_id, st.session_state.artworks_current_page)
                new_artworks = response.get('artworks', [])

                if new_artworks:
                    st.session_state.artworks_list.extend(new_artworks)
                    pagination = response.get('pagination', {})
                    st.session_state.has_more_artworks = pagination.get('current_page', 1) < pagination.get(
                        'total_pages', 1)
                else:
                    st.session_state.has_more_artworks = False

                st.rerun()
    else:
        st.warning("No artworks found for this artist.")


def display_analysis_panel():
    """Main analysis interface"""
    if not st.session_state.selected_artwork:
        return

    artwork = st.session_state.selected_artwork
    st.header(f"Details: {artwork.get('title', 'Untitled')}")

    with st.expander("Basic Information", expanded=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            image_id = artwork.get('image_id')
            st.image(
                f"https://www.artic.edu/iiif/2/{image_id}/full/800,/0/default.jpg" if image_id else PLACEHOLDER_IMAGE,
                use_container_width=True,
                caption=f"{artwork['title']} by {artwork['artist_title']}"
            )

        with col2:
            st.markdown(f"""
                **Artist:** {artwork.get('artist_title', 'Unknown')}  
                **Date:** {artwork.get('date_display', 'Unknown date')}  
                **Medium:** {artwork.get('medium_display', 'Unknown medium')}  
                **Dimensions:** {artwork.get('dimensions', 'N/A')}  
                **Style:** {', '.join(artwork.get('style_titles', ['N/A']))}
            """)

            if st.session_state.selected_artist:
                artist = st.session_state.selected_artist
                st.markdown(f"""
                **Artist Lifespan:** {artist.get('birth_date', '?')} - {artist.get('death_date', '?')}  
                """)

    # Display web research context if available
    if st.session_state.web_context:
        st.divider()
        st.subheader("Research Context")
        for idx, source in enumerate(st.session_state.web_context, 1):
            with st.expander(f"Source {idx}: {source['source']}"):
                st.write(source['content'])


def main():
    # Sidebar controls
    with st.sidebar:
        st.header("Artwork Explorer")
        
        if st.button("🔄 Start New Search", use_container_width=True):
            st.session_state.selected_artist = None
            st.session_state.selected_artwork = None
            st.session_state.web_context = []
            st.session_state.artworks_list = []
            st.session_state.artworks_current_page = 1
            st.session_state.has_more_artworks = True
            st.rerun()

        st.markdown("---")
        st.markdown("**Art Intelligence Suite**")
        st.markdown("Explore artwork from the Art Institute of Chicago")
        st.markdown("Powered by:")
        st.markdown("- Art Institute of Chicago API")
        st.markdown("- DuckDuckGo Search")

    if not st.session_state.selected_artist:
        display_artist_selection()
    elif not st.session_state.selected_artwork:
        display_artwork_analysis()
    else:
        display_analysis_panel()


if __name__ == "__main__":
    main()
