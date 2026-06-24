import { useState } from 'react'
import { useAppStore } from '../store/useAppStore'
import { cn } from '../lib/utils'
import {
  Trophy, Zap, CheckCircle2, XCircle, ChevronRight,
  BookOpen, Star, Coins, History,
} from 'lucide-react'
import type { HITLQuestion } from '../types'

const LEVEL_NAMES: Record<number, string> = {
  1: 'Market Rookie',
  2: 'Signal Reader',
  3: 'Chart Analyst',
  4: 'Macro Thinker',
  5: 'Alpha Hunter',
  20: 'FinNexus Oracle',
}

export function ContributePage() {
  const { hitlProgress, hitlQuestions, submitAnswer } = useAppStore()
  const [activeQuestion, setActiveQuestion] = useState<HITLQuestion | null>(null)
  const [selectedAnswer, setSelectedAnswer] = useState<string>('')
  const [saAnswer, setSaAnswer] = useState<string>('')
  const [submitted, setSubmitted] = useState(false)
  const [wasCorrect, setWasCorrect] = useState<boolean | null>(null)
  const [activeTab, setActiveTab] = useState<'questions' | 'history'>('questions')

  const currentLevelQuestions = hitlQuestions.filter(q => q.level === hitlProgress.currentLevel)
  const nextLevelQuestions = hitlQuestions.filter(q => q.level === hitlProgress.currentLevel + 1)

  const answeredIds = new Set(hitlProgress.history.map(h => h.questionId))
  const unanswered = currentLevelQuestions.filter(q => !answeredIds.has(q.id))

  const xpPercent = Math.round((hitlProgress.xp / hitlProgress.xpForNextLevel) * 100)

  const handleSubmit = () => {
    if (!activeQuestion) return
    const answer = activeQuestion.type === 'MCQ' ? selectedAnswer : saAnswer
    if (!answer.trim()) return

    const isCorrect = activeQuestion.type === 'MCQ'
      ? answer === activeQuestion.correctAnswer
      : answer.trim().length >= 30

    submitAnswer(activeQuestion.id, answer)
    setWasCorrect(isCorrect)
    setSubmitted(true)
  }

  const handleNext = () => {
    setActiveQuestion(null)
    setSelectedAnswer('')
    setSaAnswer('')
    setSubmitted(false)
    setWasCorrect(null)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-headline font-bold text-2xl text-on-surface">Contribute & Earn</h1>
        <p className="text-sm text-on-surface-variant mt-0.5">Answer market questions to level up and earn paper cash</p>
      </div>

      {/* Profile / Level card */}
      <div className="bg-surface-container-low rounded-xl border border-primary/15 p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center shadow-[0_0_16px_rgba(16,185,129,0.15)]">
              <Trophy size={20} className="text-primary" />
            </div>
            <div>
              <p className="font-headline font-bold text-on-surface">Level {hitlProgress.currentLevel}</p>
              <p className="text-xs text-primary font-headline">{LEVEL_NAMES[hitlProgress.currentLevel] ?? 'Trader'}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-surface-container-high rounded-lg px-3 py-2 border border-primary/15">
            <Coins size={13} className="text-primary" />
            <div>
              <p className="text-[10px] font-headline text-on-surface-variant">Earned</p>
              <p className="font-data font-bold text-primary text-sm">₹{hitlProgress.cashEarned}</p>
            </div>
          </div>
        </div>

        {/* XP bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-1.5">
              <Zap size={11} className="text-tertiary" />
              <span className="text-xs font-headline text-on-surface-variant">XP Progress</span>
            </div>
            <span className="text-xs font-data text-on-surface">{hitlProgress.xp} / {hitlProgress.xpForNextLevel}</span>
          </div>
          <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary to-primary-container rounded-full transition-all duration-500"
              style={{ width: `${xpPercent}%` }}
            />
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-3 mt-4">
          <MiniStat label="Contributions" value={hitlProgress.totalContributions} />
          <MiniStat
            label="Accuracy"
            value={hitlProgress.totalContributions > 0
              ? `${Math.round((hitlProgress.correctAnswers / hitlProgress.totalContributions) * 100)}%`
              : '–'}
          />
          <MiniStat label="Levels Done" value={hitlProgress.completedLevels.length} />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-surface-container-low rounded-lg p-1 border border-outline-variant/15 w-fit">
        {(['questions', 'history'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              'px-4 py-1.5 rounded text-xs font-headline font-semibold transition-all capitalize',
              activeTab === tab ? 'bg-primary/10 text-primary' : 'text-on-surface-variant hover:text-on-surface'
            )}
          >
            {tab === 'questions' ? 'Questions' : 'History'}
          </button>
        ))}
      </div>

      {activeTab === 'questions' && (
        <>
          {/* Active question modal-style */}
          {activeQuestion ? (
            <QuestionPanel
              question={activeQuestion}
              selectedAnswer={selectedAnswer}
              setSelectedAnswer={setSelectedAnswer}
              saAnswer={saAnswer}
              setSaAnswer={setSaAnswer}
              submitted={submitted}
              wasCorrect={wasCorrect}
              onSubmit={handleSubmit}
              onNext={handleNext}
            />
          ) : (
            <div className="space-y-4">
              {/* Current level questions */}
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <Star size={13} className="text-primary" />
                  <h2 className="text-xs font-headline font-semibold text-on-surface uppercase tracking-wider">
                    Level {hitlProgress.currentLevel} — {LEVEL_NAMES[hitlProgress.currentLevel] ?? ''}
                  </h2>
                  <span className="text-[10px] font-data text-on-surface-variant">{unanswered.length} remaining</span>
                </div>
                <div className="space-y-2">
                  {currentLevelQuestions.map(q => (
                    <QuestionRow
                      key={q.id}
                      question={q}
                      answered={answeredIds.has(q.id)}
                      onSelect={() => !answeredIds.has(q.id) && setActiveQuestion(q)}
                    />
                  ))}
                </div>
              </section>

              {/* Next level preview */}
              {nextLevelQuestions.length > 0 && (
                <section className="opacity-60">
                  <div className="flex items-center gap-2 mb-3">
                    <h2 className="text-xs font-headline font-semibold text-on-surface-variant uppercase tracking-wider">
                      Level {hitlProgress.currentLevel + 1} — Locked
                    </h2>
                  </div>
                  <div className="space-y-2">
                    {nextLevelQuestions.slice(0, 2).map(q => (
                      <QuestionRow key={q.id} question={q} answered={false} locked onSelect={() => {}} />
                    ))}
                  </div>
                </section>
              )}
            </div>
          )}
        </>
      )}

      {activeTab === 'history' && (
        <div className="bg-surface-container-low rounded-xl border border-outline-variant/15 p-4">
          <div className="flex items-center gap-2 mb-4">
            <History size={13} className="text-on-surface-variant" />
            <h2 className="font-headline font-semibold text-sm text-on-surface">Contribution History</h2>
          </div>
          {hitlProgress.history.length === 0 ? (
            <p className="text-sm text-on-surface-variant font-body text-center py-6">No contributions yet. Answer your first question!</p>
          ) : (
            <div className="space-y-2">
              {hitlProgress.history.map(h => (
                <div key={h.id} className="flex items-start gap-3 py-2.5 border-b border-outline-variant/8 last:border-0">
                  {h.correct ? (
                    <CheckCircle2 size={14} className="text-primary shrink-0 mt-0.5" />
                  ) : (
                    <XCircle size={14} className="text-error shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-headline font-medium text-on-surface truncate">{h.question}</p>
                    <p className="text-[10px] text-on-surface-variant mt-0.5 truncate">
                      You answered: "{h.userAnswer.slice(0, 60)}{h.userAnswer.length > 60 ? '...' : ''}"
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className={cn('text-xs font-data font-bold', h.correct ? 'text-primary' : 'text-error')}>
                      +₹{h.cashEarned}
                    </p>
                    <p className="text-[10px] text-on-surface-variant font-data">
                      {new Date(h.timestamp).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function MiniStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="text-center">
      <p className="font-data font-bold text-on-surface text-base">{value}</p>
      <p className="text-[10px] text-on-surface-variant font-headline uppercase tracking-wider mt-0.5">{label}</p>
    </div>
  )
}

function QuestionRow({ question: q, answered, locked, onSelect }: {
  question: HITLQuestion; answered: boolean; locked?: boolean; onSelect: () => void
}) {
  return (
    <button
      onClick={onSelect}
      disabled={answered || locked}
      className={cn(
        'w-full flex items-center gap-3 p-3.5 rounded-xl border text-left transition-all',
        answered ? 'border-primary/20 bg-primary/5 opacity-70' :
        locked ? 'border-outline-variant/10 opacity-40 cursor-not-allowed' :
        'border-outline-variant/15 hover:border-primary/20 hover:bg-surface-container-high'
      )}
    >
      {answered ? (
        <CheckCircle2 size={14} className="text-primary shrink-0" />
      ) : (
        <div className={cn('w-3.5 h-3.5 rounded-full border-2 shrink-0', locked ? 'border-outline-variant/30' : 'border-primary/40')} />
      )}
      <div className="flex-1 min-w-0">
        <p className="text-xs font-headline font-medium text-on-surface truncate">{q.question}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-[10px] font-headline text-on-surface-variant">{q.type}</span>
          <span className="text-[10px] text-on-surface-variant">·</span>
          <span className="text-[10px] font-data text-primary">+₹{q.reward}</span>
        </div>
      </div>
      {!answered && !locked && <ChevronRight size={13} className="text-on-surface-variant shrink-0" />}
    </button>
  )
}

function QuestionPanel({
  question: q,
  selectedAnswer, setSelectedAnswer,
  saAnswer, setSaAnswer,
  submitted, wasCorrect,
  onSubmit, onNext,
}: {
  question: HITLQuestion
  selectedAnswer: string; setSelectedAnswer: (v: string) => void
  saAnswer: string; setSaAnswer: (v: string) => void
  submitted: boolean; wasCorrect: boolean | null
  onSubmit: () => void; onNext: () => void
}) {
  return (
    <div className="bg-surface-container-low rounded-xl border border-outline-variant/20 p-5 space-y-4">
      {/* Context */}
      <div className="flex items-start gap-2 p-3 bg-surface-container-high rounded-lg border border-outline-variant/10">
        <BookOpen size={13} className="text-on-surface-variant shrink-0 mt-0.5" />
        <p className="text-xs text-on-surface-variant font-body">{q.context}</p>
      </div>

      {/* Question */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <span className={cn('text-[10px] font-headline font-semibold px-2 py-0.5 rounded', q.type === 'MCQ' ? 'bg-primary/10 text-primary' : 'bg-tertiary/10 text-tertiary')}>
            {q.type}
          </span>
          <span className="text-[10px] font-data text-primary">Reward: +₹{q.reward}</span>
        </div>
        <p className="font-headline font-semibold text-sm text-on-surface">{q.question}</p>
      </div>

      {/* Answer input */}
      {!submitted && (
        <>
          {q.type === 'MCQ' && q.options ? (
            <div className="space-y-2">
              {q.options.map(opt => (
                <button
                  key={opt}
                  onClick={() => setSelectedAnswer(opt)}
                  className={cn(
                    'w-full text-left p-3 rounded-lg border text-xs font-body transition-all',
                    selectedAnswer === opt
                      ? 'border-primary/50 bg-primary/5 text-on-surface'
                      : 'border-outline-variant/15 text-on-surface-variant hover:border-outline-variant/30'
                  )}
                >
                  {opt}
                </button>
              ))}
            </div>
          ) : (
            <div>
              <textarea
                value={saAnswer}
                onChange={e => setSaAnswer(e.target.value)}
                placeholder="Type your analysis here... (minimum 30 characters)"
                className="w-full bg-surface-container-high border border-outline-variant/20 rounded-lg p-3 text-xs text-on-surface placeholder-on-surface-variant/50 font-body resize-none focus:outline-none focus:border-primary/40 transition-colors"
                rows={4}
              />
              <p className="text-[10px] text-on-surface-variant mt-1 font-data">{saAnswer.length} / 30 min chars</p>
            </div>
          )}
          <button
            onClick={onSubmit}
            disabled={q.type === 'MCQ' ? !selectedAnswer : saAnswer.trim().length < 30}
            className="w-full py-2.5 rounded-lg bg-primary text-on-primary font-headline font-semibold text-sm transition-all hover:brightness-110 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Submit Answer
          </button>
        </>
      )}

      {/* Result */}
      {submitted && wasCorrect !== null && (
        <div className={cn(
          'rounded-xl border p-4 space-y-3',
          wasCorrect ? 'border-primary/30 bg-primary/5' : 'border-error/30 bg-error/5'
        )}>
          <div className="flex items-center gap-2">
            {wasCorrect ? (
              <CheckCircle2 size={16} className="text-primary" />
            ) : (
              <XCircle size={16} className="text-error" />
            )}
            <span className={cn('font-headline font-bold text-sm', wasCorrect ? 'text-primary' : 'text-error')}>
              {wasCorrect ? 'Correct! Well done.' : 'Not quite right.'}
            </span>
            <span className="text-xs font-data text-on-surface-variant ml-auto">
              +₹{wasCorrect ? q.reward : Math.floor(q.reward * 0.3)} earned
            </span>
          </div>
          {q.type === 'MCQ' && !wasCorrect && q.correctAnswer && (
            <p className="text-xs text-on-surface-variant font-body">
              Correct answer: <span className="text-on-surface font-medium">{q.correctAnswer}</span>
            </p>
          )}
          <p className="text-xs text-on-surface-variant font-body leading-relaxed">{q.context}</p>
          <button
            onClick={onNext}
            className="w-full py-2.5 rounded-lg border border-primary/30 text-primary font-headline font-semibold text-xs hover:bg-primary/5 transition-colors"
          >
            Next Question →
          </button>
        </div>
      )}
    </div>
  )
}
