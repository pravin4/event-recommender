import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css';

interface Recommendation {
  title: string;
  description: string;
  date: string;
  location: string;
  price?: string;
  categories?: string[];
  url?: string;
  relevance_score?: number;
  reasoning?: string;
  personalization?: string;
}

function App() {
  const [zipCode, setZipCode] = useState('')
  const [interests, setInterests] = useState('')
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [userLocation, setUserLocation] = useState('')

  useEffect(() => {
    // Try to get user's location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            const response = await axios.get(
              `https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.coords.latitude}&lon=${position.coords.longitude}`
            );
            const zip = response.data.address.postcode;
            setUserLocation(zip);
            setZipCode(zip);
          } catch (err) {
            console.error('Error getting location:', err);
          }
        },
        (error) => {
          console.error('Geolocation error:', error);
        }
      );
    }
  }, []);

  const parseRecommendation = (text: string): Recommendation | null => {
    // Split by newlines and filter out empty lines
    const lines = text.split('\n').filter(line => line.trim() !== '');
    
    if (lines.length < 2) {
      console.log('Invalid recommendation format:', text);
      return null;
    }

    // Extract title (remove the leading "- " if present)
    const title = lines[0].replace(/^-\s*/, '').trim();
    
    // Extract other fields
    const description = lines.find(line => line.trim().startsWith('Description:'))?.replace('Description:', '').trim() || 'No description available';
    const location = lines.find(line => line.trim().startsWith('Location:'))?.replace('Location:', '').trim() || 'Location not specified';
    const date = lines.find(line => line.trim().startsWith('Date:'))?.replace('Date:', '').trim() || 'Date not specified';
    const price = lines.find(line => line.trim().startsWith('Price:'))?.replace('Price:', '').trim();
    const categories = lines.find(line => line.trim().startsWith('Categories:'))?.replace('Categories:', '').trim().split(',').map(c => c.trim());
    
    return {
      title,
      description,
      date,
      location,
      price,
      categories
    };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setRecommendations([])

    try {
      const response = await axios.post('/api/recommendations', {
        zip_code: zipCode,
        interests: interests.split(',').map(i => i.trim())
      })
      
      console.log('Raw response:', response.data);
      
      if (Array.isArray(response.data.recommendations)) {
        setRecommendations(response.data.recommendations);
      } else {
        setError('Invalid response format from server');
        console.error('Invalid response format:', response.data);
      }
    } catch (err) {
      setError('Failed to fetch recommendations. Please try again.')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-8">Event Recommendations</h1>
        
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Zip Code</label>
            <input
              type="text"
              value={zipCode}
              onChange={(e) => setZipCode(e.target.value)}
              required
              className="form-input"
              placeholder={userLocation ? `Current location: ${userLocation}` : "Enter your zip code"}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Interests (comma-separated)</label>
            <input
              type="text"
              value={interests}
              onChange={(e) => setInterests(e.target.value)}
              placeholder="e.g., music, art, sports"
              required
              className="form-input"
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
          >
            {loading ? 'Loading...' : 'Get Recommendations'}
          </button>
        </form>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {recommendations.length > 0 && (
          <div className="mt-8 space-y-6">
            <h2 className="text-2xl font-semibold mb-6 text-center text-gray-800">Your Recommendations</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {recommendations.map((rec, index) => (
                <div key={index} className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 overflow-hidden">
                  <div className="p-6">
                    <h3 className="text-xl font-bold mb-3 text-gray-900">{rec.title}</h3>
                    <p className="text-gray-600 mb-4 line-clamp-3">{rec.description}</p>
                    
                    <div className="space-y-2 mb-4">
                      <div className="flex items-center text-sm text-gray-500">
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        {rec.date}
                      </div>
                      <div className="flex items-center text-sm text-gray-500">
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        {rec.location}
                      </div>
                      {rec.price && (
                        <div className="flex items-center text-sm text-gray-500">
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          {rec.price}
                        </div>
                      )}
                      {rec.relevance_score && (
                        <div className="flex items-center text-sm text-gray-500">
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                          </svg>
                          Relevance: {(rec.relevance_score * 100).toFixed(0)}%
                        </div>
                      )}
                    </div>

                    {rec.categories && (
                      <div className="flex flex-wrap gap-2 mb-4">
                        {Array.from(new Set(rec.categories)).map((category, i) => (
                          <span key={i} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                            {category}
                          </span>
                        ))}
                      </div>
                    )}

                    {rec.reasoning && (
                      <div className="mb-4">
                        <p className="text-sm text-gray-600 italic">
                          {rec.reasoning}
                        </p>
                      </div>
                    )}

                    {rec.personalization && (
                      <div className="mb-4">
                        <p className="text-sm text-gray-600">
                          {rec.personalization}
                        </p>
                      </div>
                    )}

                    {rec.url && rec.url !== 'N/A' && (
                      <a
                        href={rec.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
                      >
                        Get Tickets
                        <svg className="ml-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                        </svg>
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App; 