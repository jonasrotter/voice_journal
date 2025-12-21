import { Card } from '@/components/ui/card'
import { Sparkle } from '@phosphor-icons/react'

const QUESTIONS = [
  "What are you grateful for?",
  "What did you learn?",
  "What do you want to keep doing?"
]

export function GuidingQuestions() {
  return (
    <Card className="p-6 bg-gradient-to-br from-card to-secondary/20 border-secondary/40">
      <div className="flex items-start gap-3 mb-4">
        <Sparkle size={24} weight="fill" className="text-accent shrink-0 mt-1" />
        <div>
          <h3 className="font-semibold text-lg mb-1">Reflection Prompts</h3>
          <p className="text-sm text-muted-foreground">
            Consider these questions as you record
          </p>
        </div>
      </div>
      <ul className="space-y-3">
        {QUESTIONS.map((question, index) => (
          <li key={index} className="flex items-start gap-3 text-foreground/90">
            <span className="text-accent font-medium shrink-0">{index + 1}.</span>
            <span className="leading-relaxed">{question}</span>
          </li>
        ))}
      </ul>
    </Card>
  )
}
