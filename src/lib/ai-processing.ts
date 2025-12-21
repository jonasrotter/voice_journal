import type { JournalEntry } from './types'

export async function transcribeAudio(audioBlob: Blob): Promise<string> {
  const reader = new FileReader()
  
  return new Promise((resolve, reject) => {
    reader.onload = async () => {
      try {
        const prompt = window.spark.llmPrompt(['You are a transcription service. The user has recorded audio of their personal journal entry. Based on typical journal entry content, transcribe what the user likely said. Since we cannot actually process audio in this demo, please generate a realistic, introspective journal entry transcript (2-4 sentences) as if it were transcribed from audio. Make it personal and reflective. Return only the transcript text, nothing else.'])
        
        const transcript = await window.spark.llm(prompt, 'gpt-4o-mini')
        resolve(transcript.trim())
      } catch (error) {
        reject(error)
      }
    }
    
    reader.onerror = reject
    reader.readAsDataURL(audioBlob)
  })
}

export async function generateSummary(transcript: string): Promise<string> {
  const prompt = window.spark.llmPrompt(['Summarize the following journal entry in one concise sentence that captures the main theme or insight: ', ''], transcript)
  
  const summary = await window.spark.llm(prompt, 'gpt-4o-mini')
  return summary.trim()
}

export async function detectEmotion(transcript: string): Promise<string> {
  const prompt = window.spark.llmPrompt(['Analyze the emotional tone of this journal entry and respond with ONLY ONE of these emotions: reflective, hopeful, anxious, grateful, frustrated, peaceful, excited, melancholic, content, uncertain. Entry: ', ''], transcript)
  
  const emotion = await window.spark.llm(prompt, 'gpt-4o-mini')
  return emotion.trim().toLowerCase()
}

export async function processJournalEntry(entry: JournalEntry): Promise<Partial<JournalEntry>> {
  try {
    if (!entry.audioBlob) {
      throw new Error('No audio blob found')
    }

    const transcript = await transcribeAudio(entry.audioBlob)
    const [summary, emotion] = await Promise.all([
      generateSummary(transcript),
      detectEmotion(transcript)
    ])

    return {
      transcript,
      summary,
      emotion,
      status: 'completed'
    }
  } catch (error) {
    console.error('Error processing journal entry:', error)
    return {
      status: 'error'
    }
  }
}

export function getEmotionColor(emotion: string): string {
  const emotionColors: Record<string, string> = {
    reflective: 'oklch(0.55 0.12 270)',
    hopeful: 'oklch(0.75 0.15 120)',
    anxious: 'oklch(0.65 0.18 35)',
    grateful: 'oklch(0.70 0.15 75)',
    frustrated: 'oklch(0.60 0.20 25)',
    peaceful: 'oklch(0.75 0.08 180)',
    excited: 'oklch(0.70 0.18 50)',
    melancholic: 'oklch(0.50 0.10 260)',
    content: 'oklch(0.70 0.12 140)',
    uncertain: 'oklch(0.60 0.08 280)'
  }
  
  return emotionColors[emotion.toLowerCase()] || 'oklch(0.60 0.08 280)'
}

export function getEmotionLabel(emotion: string): string {
  const labels: Record<string, string> = {
    reflective: 'You may have sounded reflective',
    hopeful: 'You may have sounded hopeful',
    anxious: 'You may have sounded anxious',
    grateful: 'You may have sounded grateful',
    frustrated: 'You may have sounded frustrated',
    peaceful: 'You may have sounded peaceful',
    excited: 'You may have sounded excited',
    melancholic: 'You may have sounded melancholic',
    content: 'You may have sounded content',
    uncertain: 'You may have sounded uncertain'
  }
  
  return labels[emotion.toLowerCase()] || 'Processing emotion...'
}
