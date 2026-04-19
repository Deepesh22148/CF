document.addEventListener('DOMContentLoaded', () => {
    const recommendBtn = document.getElementById('recommendBtn');
    const userIdInput = document.getElementById('userIdInput');
    const loadingState = document.getElementById('loadingState');
    const resultsSection = document.getElementById('resultsSection');
    const userInfoContainer = document.getElementById('userInfo');
    const movieList = document.getElementById('movieList');
    
    // Allow pressing Enter in input
    userIdInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            getRecommendations();
        }
    });

    recommendBtn.addEventListener('click', getRecommendations);

    async function getRecommendations() {
        const userId = userIdInput.value;
        if (!userId || userId < 1 || userId > 943) {
            alert('Please enter a valid User ID between 1 and 943');
            return;
        }

        // UI transitions
        resultsSection.classList.add('hidden');
        loadingState.classList.remove('hidden');
        recommendBtn.disabled = true;

        try {
            const response = await fetch('/api/recommend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_id: parseInt(userId) })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to fetch recommendations');
            }

            const data = await response.json();
            renderResults(data);

        } catch (error) {
            console.error(error);
            alert(`Error: ${error.message}\nMake sure the backend is running!`);
        } finally {
            loadingState.classList.add('hidden');
            recommendBtn.disabled = false;
        }
    }

    function renderResults(data) {
        // Clear previous
        userInfoContainer.innerHTML = '';
        movieList.innerHTML = '';

        // Render User Context
        const { age, gender, occupation, liked_samples } = data.user_info;
        
        // Add demographic tags
        addTag(`${age} y/o`, false);
        addTag(gender === 'M' ? 'Male' : (gender === 'F' ? 'Female' : 'Other'), false);
        addTag(capitalizeFirstLetter(occupation), false);
        
        // Add likes
        liked_samples.forEach(movie => {
            addTag(`Liked: ${movie}`, true);
        });

        // Render Movies
        data.recommendations.forEach(rec => {
            const card = document.createElement('div');
            card.className = 'movie-card';
            
            card.innerHTML = `
                <div class="movie-title">${escapeHTML(rec.title)}</div>
                <div class="movie-genres">${escapeHTML(rec.genres)}</div>
                <div class="movie-score">
                    <i class="fa-solid fa-fire"></i>
                    Hit Likelihood: ${rec.score}%
                </div>
            `;
            movieList.appendChild(card);
        });

        // Show Results
        resultsSection.classList.remove('hidden');
    }

    function addTag(text, isHighlight) {
        const span = document.createElement('span');
        span.className = `tag ${isHighlight ? 'highlight' : ''}`;
        
        if (isHighlight) {
             span.innerHTML = `<i class="fa-solid fa-thumbs-up" style="margin-right:0.3rem"></i> ${escapeHTML(text)}`;
        } else {
             span.textContent = text;
        }
       
        userInfoContainer.appendChild(span);
    }

    function capitalizeFirstLetter(string) {
        if (!string) return '';
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }
});
