import React from 'react';
import { Link } from 'react-router-dom';
import { FiMic, FiFileText, FiVolume2, FiShield, FiGlobe, FiZap } from 'react-icons/fi';
import Navbar from '../Navbar';

export default function About() {
  return (
    <>
    <Navbar />
    <div className="min-h-screen bg-white">
      {/* Header */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-100 py-20">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            An AI practice partner built to make high-stakes conversations feel low-stakes.
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            SpeakUp pairs three engines — real-time transcription, automated grammar detection, and phonetic analysis — into one calm interface. Whether you're rehearsing for a job interview or a client kickoff, you get precise, color-coded feedback the moment you finish speaking.
          </p>
          <Link 
            to="/register"
            className="inline-block px-8 py-4 bg-primary text-white font-bold rounded-lg hover:bg-blue-700 transition"
          >
            Start Free Trial
          </Link>
        </div>
      </section>

      {/* Key Features */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-16">How the pieces fit together</h2>
          
          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <FeatureBox 
              icon={<FiMic className="w-12 h-12" />}
              title="Real-time AI Transcription"
              description="Whisper-grade speech recognition streams your words as you speak — every pause, every word captured instantly."
            />
            <FeatureBox 
              icon={<FiFileText className="w-12 h-12" />}
              title="LanguageTool Grammar"
              description="Production-grade grammar detection flags syntax errors with inline corrections and explanations."
            />
            <FeatureBox 
              icon={<FiVolume2 className="w-12 h-12" />}
              title="Phonetic Engine"
              description="IPA-based phoneme matching identifies mispronunciations at the syllable level, not just the word."
            />
          </div>

          {/* Process Steps */}
          <div className="bg-gray-50 rounded-xl p-12">
            <h3 className="text-2xl font-bold text-gray-900 mb-8">The Practice Loop</h3>
            <div className="space-y-6">
              <ProcessStep 
                number="1" 
                title="Speak" 
                description="Click to record your response to an interview question. Your voice is captured locally in your browser." 
              />
              <ProcessStep 
                number="2" 
                title="Analyze" 
                description="Grammar and phonetic engines process your speech in parallel, identifying errors without leaving your browser." 
              />
              <ProcessStep 
                number="3" 
                title="Reflect" 
                description="See color-coded feedback with corrections you can act on immediately. Re-record or move to the next question." 
              />
            </div>
          </div>
        </div>
      </section>

      {/* Why SpeakUp */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-16">Why SpeakUp?</h2>
          
          <div className="grid md:grid-cols-2 gap-8">
            <BenefitCard 
              icon={<FiZap className="w-8 h-8" />}
              title="Instant Feedback"
              description="See corrections within seconds of finishing your answer, not hours or days later."
            />
            <BenefitCard 
              icon={<FiShield className="w-8 h-8" />}
              title="Private by Design"
              description="Recordings never leave your browser. Your voice data is your own."
            />
            <BenefitCard 
              icon={<FiGlobe className="w-8 h-8" />}
              title="Browser Native"
              description="No downloads, no installations. Works on any device with a modern web browser."
            />
            <BenefitCard 
              icon={<FiFileText className="w-8 h-8" />}
              title="Role Specific"
              description="Choose from 10+ industries and 10+ roles. Questions are tailored to your context."
            />
          </div>
        </div>
      </section>

      {/* Comparison */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-16">How SpeakUp Compares</h2>
          
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="px-6 py-4 text-left font-bold text-gray-900">Feature</th>
                  <th className="px-6 py-4 text-center font-bold text-gray-900">SpeakUp</th>
                  <th className="px-6 py-4 text-center font-bold text-gray-900">Competitor A</th>
                  <th className="px-6 py-4 text-center font-bold text-gray-900">Competitor B</th>
                </tr>
              </thead>
              <tbody>
                <TableRow 
                  feature="Real-time Transcription" 
                  speakup={true} 
                  compA={true} 
                  compB={false} 
                />
                <TableRow 
                  feature="Grammar Detection" 
                  speakup={true} 
                  compA={false} 
                  compB={true} 
                />
                <TableRow 
                  feature="Pronunciation Analysis" 
                  speakup={true} 
                  compA={false} 
                  compB={false} 
                />
                <TableRow 
                  feature="Role-Specific Questions" 
                  speakup={true} 
                  compA={true} 
                  compB={true} 
                />
                <TableRow 
                  feature="Free to Use" 
                  speakup={true} 
                  compA={false} 
                  compB={false} 
                />
                <TableRow 
                  feature="Privacy (No Storage)" 
                  speakup={true} 
                  compA={false} 
                  compB={false} 
                />
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-primary text-white">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold mb-6">Ready to master your next interview?</h2>
          <p className="text-xl mb-8 text-blue-100">
            Join thousands of professionals who use SpeakUp to build confidence and improve their communication skills.
          </p>
          <Link 
            to="/register"
            className="inline-block px-8 py-4 bg-white text-primary font-bold rounded-lg hover:bg-gray-100 transition"
          >
            Start Free Today
          </Link>
        </div>
      </section>
    </div>
    </>
  );
}

function FeatureBox({ icon, title, description }) {
  return (
    <div className="p-8 bg-gray-50 rounded-xl border border-gray-200 hover:shadow-lg transition">
      <div className="text-primary mb-4">{icon}</div>
      <h3 className="text-xl font-bold text-gray-900 mb-3">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

function ProcessStep({ number, title, description }) {
  return (
    <div className="flex gap-6">
      <div className="flex-shrink-0">
        <div className="flex items-center justify-center h-12 w-12 rounded-full bg-primary text-white font-bold text-lg">
          {number}
        </div>
      </div>
      <div>
        <h4 className="text-lg font-bold text-gray-900 mb-2">{title}</h4>
        <p className="text-gray-600">{description}</p>
      </div>
    </div>
  );
}

function BenefitCard({ icon, title, description }) {
  return (
    <div className="p-6 bg-white rounded-xl border border-gray-200 hover:shadow-lg transition">
      <div className="text-primary mb-4">{icon}</div>
      <h3 className="text-lg font-bold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

function TableRow({ feature, speakup, compA, compB }) {
  const CheckMark = () => <span className="text-success font-bold">✓</span>;
  const XMark = () => <span className="text-error font-bold">✗</span>;
  
  return (
    <tr className="border-b border-gray-200 hover:bg-gray-50">
      <td className="px-6 py-4 font-semibold text-gray-900">{feature}</td>
      <td className="px-6 py-4 text-center">{speakup ? <CheckMark /> : <XMark />}</td>
      <td className="px-6 py-4 text-center">{compA ? <CheckMark /> : <XMark />}</td>
      <td className="px-6 py-4 text-center">{compB ? <CheckMark /> : <XMark />}</td>
    </tr>
  );
}