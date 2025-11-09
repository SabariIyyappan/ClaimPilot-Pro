import axios from 'axios';
import type {
  UploadResponse,
  SuggestRequest,
  SuggestResponse,
  GenerateClaimRequest,
  GenerateClaimResponse,
  CMS1500Request,
  CodeSuggestion,
} from './types';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  timeout: 120000,
  // Do not set a global Content-Type; let axios set it per request
});

export const uploadText = async (text: string): Promise<UploadResponse> => {
  const { data } = await api.post<UploadResponse>('/upload', { text });
  return data;
};

export const uploadFile = async (file: File, clinicalOnly = true, autoSuggest = false): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('clinical_only', String(clinicalOnly));
  if (autoSuggest) formData.append('auto_suggest', 'true');
  
  const { data } = await api.post<UploadResponse>('/upload', formData);
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

export const downloadCms1500 = async (req: CMS1500Request): Promise<Blob> => {
  const response = await api.post('/cms1500', req, { responseType: 'blob' });
  return response.data as Blob;
};

export const downloadClaimPdf = async (approved: CodeSuggestion[]): Promise<Blob> => {
  const response = await api.post('/claim_pdf', { approved }, { responseType: 'blob' });
  return response.data as Blob;
};

// Derive CMS-1500 header fields from uploaded/parsed text
export const deriveCms1500 = async (text: string): Promise<{
  patient_name?: string;
  patient_id?: string;
  provider_name?: string;
  date_of_service?: string;
  patient_dob?: string;
  patient_sex?: string;
  patient_address?: string;
  place_of_service?: string;
  referring_npi?: string;
}> => {
  const { data } = await api.post('/cms1500/derive', { text });
  return data as any;
};
