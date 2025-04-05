import axios from 'axios';
import { RecommendationRequest, RecommendationResponse } from '../types/Event';

const API_BASE_URL = 'http://localhost:8081';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  }
});

export const getRecommendations = async (request: RecommendationRequest): Promise<RecommendationResponse> => {
  try {
    console.log('Sending request to API:', request);
    const response = await api.post('/api/recommendations', request);
    console.log('API response:', response.data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorMessage = error.response?.data?.message || error.message;
      console.error('API Error:', {
        message: errorMessage,
        response: error.response?.data,
        status: error.response?.status,
      });
      throw new Error(`Failed to get recommendations: ${errorMessage}`);
    }
    console.error('Unexpected error:', error);
    throw new Error('An unexpected error occurred while fetching recommendations');
  }
}; 