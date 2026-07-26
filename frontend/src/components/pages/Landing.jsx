import React, { Suspense } from 'react';
import { Link } from 'react-router-dom';
import { FiArrowRight, FiMic, FiFileText, FiVolume2 } from 'react-icons/fi';
import SplineBackground from '../SplineBackground';
import Navbar from '../Navbar';

export default function Landing() {
  return (
    <>
    <Navbar />
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-100 overflow-hidden">
      <div className="absolute inset-0 w-full h-full">
     <SplineBackground />
      </div>
        
        <div className="relative z-10 max-w-7xl mx-auto px-4 h-screen flex items-center">
          <div className="grid md:grid-cols-2 gap-8 items-center w-full">
            {/* Left Content */}
            <div className="space-y-6">
              <div className="text-sm text-primary font-semibold bg-blue-50 px-3 py-1 rounded-full w-fit">
                🎤 Real-time AI Feedback
              </div>
              
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight">
                Master Your Next Interview with Real-Time AI Feedback.
              </h1>
              
              <p className="text-lg text-gray-300 max-w-xl">
                SpeakUp listens as you practice — flagging grammar slips and pronunciation deviations as they happen. Choose between <span className="font-bold">Interview Practice</span> for industry-specific questions, or <span className="font-bold">Client Meeting Practice</span> for professional conversations.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Link 
                  to="/register" 
                  className="px-8 py-3 bg-primary text-white rounded-lg font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2"
                >
                  Start Practicing For Free
                  <FiArrowRight />
                </Link>
                <Link 
                  to="/about" 
                  className="px-8 py-3 border-2 border-primary text-primary rounded-lg font-semibold hover:bg-blue-50 transition text-center"
                >
                  See how it works
                </Link>
              </div>

              {/* Trust Badge */}
              <div className="flex items-center gap-2 text-gray-600 text-sm pt-4">
                <div className="flex -space-x-2">
                  {['🧑', '👩', '👨'].map((emoji, i) => (
                    <span key={i} className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-lg">
                      {emoji}
                    </span>
                  ))}
                </div>
                <span className='text-gray-300'>Join 5,000+ job seekers already practicing</span>
              </div>
            </div>

            {/* Right - Empty space for Spline animation */}
            <div className="hidden lg:block h-full relative">
              {/* Spline animation renders here */}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-4">Why SpeakUp?</h2>
          <p className="text-center text-gray-600 mb-16 max-w-2xl mx-auto">
            Everything you need to ace interviews and client meetings with confidence.
          </p>
          
          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard 
              icon={<FiMic className="w-8 h-8" />}
              title="Real-time Transcription"
              description="Speech-to-text streams your words as you speak — every pause, every word captured instantly with high accuracy."
            />
            <FeatureCard 
              icon={<FiFileText className="w-8 h-8" />}
              title="Grammar Detection"
              description="LanguageTool engine flags syntax errors with inline corrections and explanations."
            />
            <FeatureCard 
              icon={<FiVolume2 className="w-8 h-8" />}
              title="Phonetic Analysis"
              description="IPA-based phoneme matching identifies mispronunciations at the syllable level, not just the word."
            />
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-16">How it works</h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <StepCard step="1" title="Speak" description="Click to record your response to an interview question. Your voice is captured locally." />
            <StepCard step="2" title="Analyze" description="Grammar and phonetic engines process your speech in parallel, identifying errors." />
            <StepCard step="3" title="Reflect" description="See color-coded feedback with corrections you can act on immediately." />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary text-white">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold mb-6">Ready to ace your next interview?</h2>
          <p className="text-xl mb-8 text-blue-100">
            Join thousands of professionals who use SpeakUp to build confidence and improve their communication skills.
          </p>
          <Link 
            to="/register"
            className="inline-block px-8 py-4 bg-white text-primary font-bold rounded-lg hover:bg-gray-100 transition"
          >
            Start Free Trial
          </Link>
        </div>
      </section>
    </div>
    </>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="p-6 border border-gray-200 rounded-xl hover:shadow-lg transition bg-white">
      <div className="text-primary mb-4">{icon}</div>
      <h3 className="text-xl font-bold mb-2 text-gray-900">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

function StepCard({ step, title, description }) {
  return (
    <div className="text-center">
      <div className="inline-block w-16 h-16 bg-primary text-white rounded-full flex items-center justify-center text-2xl font-bold mb-4">
        {step}
      </div>
      <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}