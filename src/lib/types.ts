export type ProcessingStatus = 'recording' | 'uploading' | 'processing' | 'completed' | 'error'

export interface JournalEntry {
  id: string
  audioBlob?: Blob
  audioUrl?: string
  transcript?: string
  summary?: string
  emotion?: string
  status: ProcessingStatus
  createdAt: number
  duration?: number
}

export interface EmotionLabel {
  label: string
  color: string
  description: string
}
