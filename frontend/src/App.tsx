import { useState, useEffect } from 'react'
import { getRecommendations } from './services/api'
import { Event, RecommendationRequest } from './types/Event'

function App() {
  const [preferences, setPreferences] = useState<RecommendationRequest>({
    zip_code: '',
    interests: []
  });
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [interestsInput, setInterestsInput] = useState('');

  // Load saved preferences on component mount
  useEffect(() => {
    const savedZipCode = localStorage.getItem('zipCode');
    const savedInterests = localStorage.getItem('interests');
    if (savedZipCode) setPreferences({ ...preferences, zip_code: savedZipCode });
    if (savedInterests) setPreferences({ ...preferences, interests: JSON.parse(savedInterests) });
  }, []);

  // Save preferences whenever they change
  useEffect(() => {
    localStorage.setItem('zipCode', preferences.zip_code);
    localStorage.setItem('interests', JSON.stringify(preferences.interests));
  }, [preferences.zip_code, preferences.interests]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    // Validate inputs
    if (!preferences.zip_code.trim()) {
      setError('Please enter your zip code');
      setLoading(false);
      return;
    }

    try {
      const response = await getRecommendations(preferences);
      setEvents(response.recommendations);
      if (response.recommendations.length === 0) {
        setError('No events found in your area. Try adjusting your zip code.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch recommendations. Please try again.');
      console.error('Error in handleSubmit:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGetLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            // Use OpenStreetMap Nominatim API to get the ZIP code
            const response = await fetch(
              `https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.coords.latitude}&lon=${position.coords.longitude}&addressdetails=1`
            );
            const data = await response.json();
            
            // Find the ZIP code in the address components
            const zipCode = data.address?.postcode;
            
            if (zipCode) {
              setPreferences({ ...preferences, zip_code: zipCode });
            } else {
              setError('Could not find ZIP code for your location');
            }
          } catch (err) {
            setError('Failed to get location information');
            console.error(err);
          }
        },
        (error) => {
          setError('Please enable location access to use this feature');
          console.error(error);
        }
      );
    } else {
      setError('Geolocation is not supported by your browser');
    }
  };

  const handleAddInterest = () => {
    if (interestsInput.trim()) {
      setPreferences(prev => ({
        ...prev,
        interests: [...prev.interests, interestsInput.trim()]
      }));
      setInterestsInput('');
    }
  };

  const handleRemoveInterest = (index: number) => {
    setPreferences(prev => ({
      ...prev,
      interests: prev.interests.filter((_, i) => i !== index)
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Event Recommender</h1>
          <p className="text-lg text-gray-600">Discover events in your area</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="zipCode" className="block text-sm font-medium text-gray-700 mb-2">
                Your Location (ZIP Code)
              </label>
              <div className="flex space-x-4">
                <input
                  type="text"
                  id="zipCode"
                  value={preferences.zip_code}
                  onChange={(e) => setPreferences({ ...preferences, zip_code: e.target.value })}
                  className="flex-1 rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="Enter your ZIP code"
                  required
                />
                <button
                  type="button"
                  onClick={handleGetLocation}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Use My Location
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Interests
              </label>
              <div className="flex space-x-4 mb-4">
                <input
                  type="text"
                  value={interestsInput}
                  onChange={(e) => setInterestsInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddInterest()}
                  className="flex-1 rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="Enter an interest (e.g., music, art, sports)"
                />
                <button
                  type="button"
                  onClick={handleAddInterest}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Add Interest
                </button>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {preferences.interests.map((interest) => (
                  <div key={interest} className="flex items-center justify-between bg-blue-100 rounded-lg px-4 py-2">
                    <span className="text-sm font-medium text-blue-800">{interest}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveInterest(preferences.interests.indexOf(interest))}
                      className="ml-2 text-blue-600 hover:text-blue-800 focus:outline-none"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-center">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Finding Events...
                  </>
                ) : (
                  'Find Events'
                )}
              </button>
            </div>
          </form>
        </div>

        {error && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-8">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {events.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {events.map((event, index) => (
              <div key={index} className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300">
                <div className="p-6">
                  <div className="flex flex-col h-full">
                    <h3 className="text-xl font-semibold text-gray-900 mb-3 line-clamp-2">{event.name}</h3>
                    
                    <div className="flex items-center text-gray-600 mb-4">
                      <svg className="w-5 h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span className="text-sm">{event.date_venue}</span>
                    </div>

                    {event.reasoning && (
                      <div className="mb-4">
                        <p className="text-sm text-gray-600 line-clamp-3">{event.reasoning}</p>
                      </div>
                    )}

                    {Object.entries(event.details).length > 0 && (
                      <div className="mb-4 space-y-1">
                        {Object.entries(event.details).map(([key, value]) => (
                          <div key={key} className="text-sm text-gray-600">
                            <span className="font-medium">{key}:</span> {value}
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="mt-auto pt-4">
                      <a
                        href={`https://www.google.com/search?q=${encodeURIComponent(event.name + ' ' + event.date_venue + ' tickets')}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center justify-center w-full px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        Get Tickets
                        <svg className="ml-2 -mr-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                        </svg>
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App; 