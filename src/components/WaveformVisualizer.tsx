import { useEffect, useRef } from 'react'

interface WaveformVisualizerProps {
  isRecording: boolean
}

export function WaveformVisualizer({ isRecording }: WaveformVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (!isRecording || !canvasRef.current) {
      return
    }

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const bars = 40
    let animationId: number

    const draw = () => {
      ctx.fillStyle = 'transparent'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      const barWidth = canvas.width / bars
      const centerY = canvas.height / 2

      for (let i = 0; i < bars; i++) {
        const variation = Math.sin(Date.now() / 200 + i) * 0.5 + 0.5
        const height = (canvas.height * 0.6 * variation) / 2

        const gradient = ctx.createLinearGradient(0, centerY - height, 0, centerY + height)
        gradient.addColorStop(0, 'oklch(0.68 0.18 25 / 0.6)')
        gradient.addColorStop(0.5, 'oklch(0.68 0.18 25)')
        gradient.addColorStop(1, 'oklch(0.68 0.18 25 / 0.6)')

        ctx.fillStyle = gradient
        ctx.fillRect(
          i * barWidth + barWidth * 0.2,
          centerY - height,
          barWidth * 0.6,
          height * 2
        )
      }

      animationId = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId)
      }
    }
  }, [isRecording])

  if (!isRecording) return null

  return (
    <div className="w-full max-w-xl animate-in fade-in">
      <canvas
        ref={canvasRef}
        width={600}
        height={100}
        className="h-20 w-full rounded-lg"
      />
    </div>
  )
}
