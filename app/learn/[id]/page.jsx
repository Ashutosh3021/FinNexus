'use client';

import React, { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { mockLessons } from '@/lib/mockData';
import { ArrowLeft, CheckCircle, Clock } from 'lucide-react';

export default function LessonPage() {
  const router = useRouter();
  const params = useParams();
  const lesson = mockLessons.find((l) => l.id === params.id);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [quizComplete, setQuizComplete] = useState(false);

  if (!lesson) {
    return (
      <div className="p-6">
        <p className="text-slate-400">Lesson not found</p>
      </div>
    );
  }

  const currentQuestion = lesson.quiz[currentQuestionIndex];
  const allAnswered = lesson.quiz.every((q) => answers[q.id] !== undefined);

  const handleAnswerSelect = (questionId, optionIndex) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: optionIndex,
    }));
  };

  const handleSubmitQuiz = () => {
    setQuizComplete(true);
  };

  const calculateScore = () => {
    let correct = 0;
    lesson.quiz.forEach((q) => {
      if (answers[q.id] === q.correct) {
        correct++;
      }
    });
    return Math.round((correct / lesson.quiz.length) * 100);
  };

  if (quizComplete) {
    const score = calculateScore();
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-blue-400 hover:text-blue-300 mb-6"
        >
          <ArrowLeft size={20} />
          Back
        </button>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center">
          <div className="mb-6">
            <div className="w-24 h-24 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle size={48} className="text-green-500" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-2">Quiz Complete!</h2>
            <p className="text-slate-400">Great job! Here's your score:</p>
          </div>

          <div className="bg-slate-700/50 rounded-lg p-6 mb-6">
            <div className="text-5xl font-bold text-blue-500 mb-2">
              {score}%
            </div>
            <p className="text-slate-300">
              You answered {lesson.quiz.filter((q) => answers[q.id] === q.correct).length} out of{' '}
              {lesson.quiz.length} questions correctly
            </p>
          </div>

          <div className="space-y-3">
            <button
              onClick={() => router.push('/learn')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition-colors"
            >
              Back to Lessons
            </button>
            <button
              onClick={() => setQuizComplete(false)}
              className="w-full bg-slate-700 hover:bg-slate-600 text-white font-semibold py-3 rounded-lg transition-colors"
            >
              Retake Quiz
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      {/* Header */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-blue-400 hover:text-blue-300 mb-6"
      >
        <ArrowLeft size={20} />
        Back to Lessons
      </button>

      {/* Lesson Title */}
      <div className="mb-8">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">{lesson.title}</h1>
            <div className="flex items-center gap-4 text-slate-400">
              <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-sm font-medium">
                {lesson.level}
              </span>
              <div className="flex items-center gap-2">
                <Clock size={16} />
                {lesson.duration}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content Section */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 mb-8">
        <h2 className="text-xl font-bold text-white mb-4">Lesson Content</h2>
        <div className="text-slate-300 space-y-4 whitespace-pre-line">
          {lesson.content}
        </div>
      </div>

      {/* Quiz Section */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-8">
        <div className="mb-6">
          <h2 className="text-xl font-bold text-white mb-4">Quiz</h2>
          <div className="flex items-center justify-between">
            <p className="text-slate-400">
              Question {currentQuestionIndex + 1} of {lesson.quiz.length}
            </p>
            <div className="w-48 bg-slate-700 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{
                  width: `${
                    ((currentQuestionIndex + 1) / lesson.quiz.length) *
                    100
                  }%`,
                }}
              ></div>
            </div>
          </div>
        </div>

        {currentQuestion && (
          <div>
            <h3 className="text-lg font-semibold text-white mb-6">
              {currentQuestion.question}
            </h3>

            <div className="space-y-3 mb-8">
              {currentQuestion.options.map((option, index) => (
                <button
                  key={index}
                  onClick={() => handleAnswerSelect(currentQuestion.id, index)}
                  className={`w-full p-4 rounded-lg text-left transition-colors ${
                    answers[currentQuestion.id] === index
                      ? 'bg-blue-600 text-white border border-blue-400'
                      : 'bg-slate-700 text-slate-300 border border-slate-600 hover:bg-slate-600'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        answers[currentQuestion.id] === index
                          ? 'bg-white border-white'
                          : 'border-slate-400'
                      }`}
                    >
                      {answers[currentQuestion.id] === index && (
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                      )}
                    </div>
                    <span>{option}</span>
                  </div>
                </button>
              ))}
            </div>

            {/* Navigation Buttons */}
            <div className="flex gap-4">
              <button
                onClick={() => setCurrentQuestionIndex(Math.max(0, currentQuestionIndex - 1))}
                disabled={currentQuestionIndex === 0}
                className="px-6 py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 text-white rounded-lg transition-colors"
              >
                Previous
              </button>

              {currentQuestionIndex === lesson.quiz.length - 1 ? (
                <button
                  onClick={handleSubmitQuiz}
                  disabled={!allAnswered}
                  className="ml-auto px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white rounded-lg transition-colors font-semibold"
                >
                  Submit Quiz
                </button>
              ) : (
                <button
                  onClick={() => setCurrentQuestionIndex(currentQuestionIndex + 1)}
                  className="ml-auto px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  Next
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
