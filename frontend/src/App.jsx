import React, { useState } from 'react';
import { Phone, CheckCircle, Rocket, Shield, Database, Zap } from 'lucide-react';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/$/, '');
const LEAD_ENDPOINT = API_BASE ? `${API_BASE}/api/leads/` : '/api/leads/';

export default function App() {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!/^09[0-9]{9}$/.test(phoneNumber)) {
      setErrorMessage('Invalid phone number format. Use 09123456789.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);

    try {
      const response = await fetch(LEAD_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phone: phoneNumber.trim() }),
        signal: controller.signal,
      });

      clearTimeout(timeout);

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || 'Submission failed, please try again.');
      }

      setSubmitted(true);
      setTimeout(() => {
        setPhoneNumber('');
        setSubmitted(false);
      }, 3000);
    } catch (error) {
      if (error.name === 'AbortError') {
        setErrorMessage('Request timed out. Please try again.');
      } else {
        setErrorMessage(error.message || 'Unexpected error. Please retry.');
      }
    } finally {
      clearTimeout(timeout);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white">
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/20 to-purple-900/20">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-full h-full bg-gradient-to-br from-blue-600/10 via-transparent to-purple-600/10" />
          </div>
        </div>

        <div className="relative z-10 container mx-auto px-4 py-24">
          <div className="max-w-4xl mx-auto text-center">
            <div>
              <h1 className="text-4xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Lightning-Fast Registration
              </h1>
              <p className="text-xl md:text-2xl text-slate-300 mb-12 max-w-2xl mx-auto">
                Experience our high-performance platform designed for millions of users
              </p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-lg rounded-2xl border border-slate-700 p-8 shadow-2xl max-w-md mx-auto">
              {!submitted ? (
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="space-y-2">
                    <label htmlFor="phone" className="block text-sm font-medium text-slate-300">
                      Enter your mobile number
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                        <Phone className="h-5 w-5 text-slate-400" />
                      </div>
                      <input
                        type="tel"
                        id="phone"
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                        placeholder="09123456789"
                        className="w-full pl-10 pr-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-slate-400"
                        required
                        pattern="09[0-9]{9}"
                        maxLength={11}
                      />
                    </div>
                    <p className="text-xs text-slate-400 text-right">Example: 09123456789</p>
                  </div>

                  {errorMessage && (
                    <p className="text-sm text-red-400 text-center" role="status">
                      {errorMessage}
                    </p>
                  )}

                  <button
                    type="submit"
                    disabled={isSubmitting || !/^09[0-9]{9}$/.test(phoneNumber)}
                    className="w-full py-3 px-6 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl font-bold text-white shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                  >
                    {isSubmitting ? (
                      <div className="flex items-center">
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                        Processing...
                      </div>
                    ) : (
                      'Submit'
                    )}
                  </button>
                </form>
              ) : (
                <div className="text-center py-6" aria-live="polite">
                  <CheckCircle className="h-16 w-16 text-green-400 mx-auto mb-4" />
                  <h3 className="text-2xl font-bold mb-2">Your number has been registered successfully!</h3>
                  <p className="text-slate-300">We&apos;ll contact you shortly</p>
                </div>
              )}
            </div>

            <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
              {[
                { icon: <Zap className="h-6 w-6" />, value: '< 1s', label: 'Page Load Time' },
                { icon: <Database className="h-6 w-6" />, value: '10M+', label: 'Successful Users' },
                { icon: <Shield className="h-6 w-6" />, value: '100%', label: 'Data Security' },
                { icon: <Rocket className="h-6 w-6" />, value: '99.99%', label: 'Uptime' },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-4 border border-slate-700/50 hover:transform hover:scale-105 transition-transform duration-300"
                >
                  <div className="flex items-center justify-center mb-2 text-blue-400">{stat.icon}</div>
                  <div className="text-2xl font-bold text-white">{stat.value}</div>
                  <div className="text-sm text-slate-400">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <footer className="py-8 text-center text-slate-500 text-sm">
        <p>© 2025 High-Traffic Landing Platform. All rights reserved.</p>
      </footer>
    </div>
  );
}
