import axios from 'axios';
import type {
  UploadResponse,
  SuggestRequest,
  SuggestResponse,
  GenerateClaimRequest,
  GenerateClaimResponse,
} from './types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadText = async (text: string): Promise<UploadResponse> => {
  const { data } = await api.post<UploadResponse>('/upload', { text });
  return data;
};

export const uploadFile = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const { data } = await api.post<UploadResponse>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const getSuggestions = async (request: SuggestRequest): Promise<SuggestResponse> => {
  const { data } = await api.post<SuggestResponse>('/suggest', request);
  return data;
};

export const generateClaim = async (request: GenerateClaimRequest): Promise<GenerateClaimResponse> => {
  const { data } = await api.post<GenerateClaimResponse>('/generate_claim', request);
  return data;
};
