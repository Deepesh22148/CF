'use client'
import React, { useState, KeyboardEvent } from "react"

interface UserInfo {
  age: number
  gender: string
  occupation: string
  liked_samples: string[]
}

interface Recommendation {
  movie_id: number
  title: string
  genres: string
  score: number
}

interface RecommendResponse {
  user_info: UserInfo
  recommendations: Recommendation[]
  rate_limited: boolean
}

const DatasetModePage = () => {
  const [userId, setUserId] = useState<string>("1")
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<RecommendResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const getRecommendations = async () => {
    const id = parseInt(userId)
    if (!userId || id < 1 || id > 943) {
      setError("Enter valid User ID (1–943)")
      return
    }

    setError(null)
    setResults(null)
    setLoading(true)

    try {
      const res = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: "dataset", user_id: id }),
      })

      if (!res.ok) throw new Error("Failed to fetch")

      const data: RecommendResponse = await res.json()
      setResults(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") getRecommendations()
  }

  const formatGender = (g: string) =>
    g === "M" ? "Male" : g === "F" ? "Female" : "Other"

  const capitalize = (s: string) =>
    s ? s.charAt(0).toUpperCase() + s.slice(1) : ""

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex items-center justify-center p-6">
      <div className="w-full max-w-5xl">

        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold bg-linear-to-r from-white to-slate-400 bg-clip-text text-transparent flex justify-center items-center gap-3">
            <span className="text-purple-400">🧠</span>
            Neural Recommender
          </h1>
          <p className="text-slate-400 mt-2">
            Personalized movie recommendations
          </p>
        </div>

        {/* Card */}
        <div className="bg-slate-800/70 backdrop-blur-lg border border-white/10 rounded-2xl p-8 shadow-xl">

          {/* Input */}
          <div className="mb-6">
            <label className="block text-sm font-semibold mb-2">
              Select User ID (1–943)
            </label>

            <div className="flex gap-4 flex-col sm:flex-row">
              <input
                type="number"
                min={1}
                max={943}
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                onKeyDown={handleKeyPress}
                className="flex-1 bg-black/30 border border-white/10 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />

              <button
                onClick={getRecommendations}
                disabled={loading}
                className="bg-linear-to-r from-purple-500 to-blue-500 px-6 py-3 rounded-lg font-semibold hover:scale-105 active:scale-95 transition disabled:opacity-50"
              >
                Get Recommendations ✨
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-500/10 border border-red-400/30 text-red-300 px-4 py-2 rounded-lg mb-4 text-sm">
              {error}
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="flex flex-col items-center py-10 text-slate-400">
              <div className="flex gap-2 mb-4">
                <div className="w-3 h-3 bg-purple-500 rounded-full animate-bounce" />
                <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce delay-150" />
                <div className="w-3 h-3 bg-pink-500 rounded-full animate-bounce delay-300" />
              </div>
              <p>Generating recommendations...</p>
            </div>
          )}

          {/* Results */}
          {results && !loading && results.user_info && (
            <>
              {/* Profile */}
              <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4 mb-6">
                <h3 className="font-semibold mb-3">👤 Profile</h3>
                <div className="flex flex-wrap gap-2">
                  <span className="px-3 py-1 bg-white/10 rounded-full text-sm">
                    {results.user_info.age} y/o
                  </span>
                  <span className="px-3 py-1 bg-white/10 rounded-full text-sm">
                    {formatGender(results.user_info.gender)}
                  </span>
                  <span className="px-3 py-1 bg-white/10 rounded-full text-sm">
                    {capitalize(results.user_info.occupation)}
                  </span>

                  {results.user_info.liked_samples.map((m, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full text-sm"
                    >
                      👍 {m}
                    </span>
                  ))}
                </div>
              </div>

              {/* Movies */}
              <h3 className="font-semibold mb-4">Top Matches</h3>

              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {results.recommendations.map((rec) => (
                  <div
                    key={rec.movie_id}
                    className="bg-black/30 border border-white/10 rounded-xl p-4 hover:-translate-y-1 hover:bg-white/5 transition"
                  >
                    <h4 className="font-bold text-lg">{rec.title}</h4>
                    <p className="text-slate-400 text-sm">
                      {rec.genres}
                    </p>

                    <div className="mt-3 text-green-400 bg-green-500/10 px-3 py-1 rounded-lg text-sm inline-block">
                      🔥 {rec.score}%
                    </div>
                  </div>
                ))}
              </div>

              {results.rate_limited && (
                <p className="text-yellow-400 text-xs text-center mt-4">
                  ⚠️ Rate limited — fallback model used
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default DatasetModePage