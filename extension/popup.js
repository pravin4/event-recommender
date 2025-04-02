document.getElementById('getRecommendations').addEventListener('click', async () => {
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const interests = document.getElementById('interests').value.split(',').map(i => i.trim());
    
    if (!interests.length) {
        alert('Please enter at least one interest');
        return;
    }
    
    loading.style.display = 'block';
    results.style.display = 'none';
    
    try {
        // Get user's location
        const position = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject);
        });
        
        // Convert coordinates to zip code using reverse geocoding
        const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.coords.latitude}&lon=${position.coords.longitude}`
        );
        const data = await response.json();
        const zipCode = data.address.postcode;
        
        // Get recommendations from our API
        const recommendationsResponse = await fetch('YOUR_API_ENDPOINT/api/recommendations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                zip_code: zipCode,
                interests: interests
            })
        });
        
        const recommendationsData = await recommendationsResponse.json();
        
        if (recommendationsResponse.ok) {
            results.innerHTML = recommendationsData.recommendations.replace(/\n/g, '<br>');
            results.style.display = 'block';
        } else {
            alert(recommendationsData.error || 'An error occurred');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        loading.style.display = 'none';
    }
}); 