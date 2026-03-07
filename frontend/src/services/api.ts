import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export interface AskResponse {
  answer: string
  sources: Array<{
    text: string
    source: string
  }>
}

export const apiService = {
  async ask(question: string): Promise<AskResponse> {
    try {
      const response = await apiClient.post<AskResponse>('/ask', { question })
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`API Error: ${error.message}`)
      }
      throw error
    }
  }
}
