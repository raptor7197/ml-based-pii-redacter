import { useState, useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { GsapTextFlip } from './components/ui/GsapTextFlip.jsx'

function App() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadState, setUploadState] = useState('idle') // 'idle', 'uploading', 'success', 'error'
  const [dragActive, setDragActive] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [showResults, setShowResults] = useState(false)
  const featuresRef = useRef(null)
  const badgesRef = useRef(null)
  const appRef = useRef(null)

  // Page load animation
  useEffect(() => {
    if (appRef.current) {
      gsap.from(appRef.current, {
        duration: 1,
        opacity: 0,
        y: 20,
        ease: 'power2.out'
      });
    }
  }, []);

  // Scroll animations
  useEffect(() => {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          gsap.from(entry.target, {
            duration: 0.8,
            opacity: 0,
            y: 30,
            ease: 'power2.out'
          });
        }
      })
    }, observerOptions)

    if (featuresRef.current) {
      const featureCards = featuresRef.current.querySelectorAll('.feature-card')
      featureCards.forEach((card, index) => {
        card.style.transitionDelay = `${index * 150}ms`
        observer.observe(card)
      })
    }

    if (badgesRef.current) {
      const badges = badgesRef.current.querySelectorAll('.security-badge')
      badges.forEach(badge => observer.observe(badge))
    }

    return () => observer.disconnect()
  }, [])

  const handleInputChange = (event) => {
    const selectedFile = event.target.files[0]
    handleFileSelect(selectedFile)
  }

  const handleFileSelect = (selectedFile) => {
    if (selectedFile) {
      setFile(selectedFile)
      setUploadState('idle')
      setError(null)
      // Don't reset result and showResults here to keep previous results visible
    }
  }

  // Drag and drop handlers
  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setLoading(true)
    setUploadState('uploading')
    setUploadProgress(0)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      // Simulate progress animation
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      // Use environment variable for API URL, fallback to localhost for development have to change in deployment 
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/upload`, {
        method: 'POST',
        body: formData
      })

      clearInterval(progressInterval)
      setUploadProgress(100)

      if (response.ok) {
        const data = await response.json()
        setResult(data)
        setShowResults(true)
        setUploadState('success')
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Upload failed')
        setUploadState('error')
      }
    } catch (err) {
      setError('Connection error. Make sure backend is running on port 8000')
      setUploadState('error')
    } finally {
      setLoading(false)
      setTimeout(() => setUploadProgress(0), 1000)
    }
  }

  const resetUpload = () => {
    setFile(null)
    setUploadState('idle')
    setUploadProgress(0)
    setLoading(false)
    setResult(null)
    setShowResults(false)
    setError(null)
  }

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
  }

  const downloadText = (text, filename) => {
    const element = document.createElement("a")
    const file = new Blob([text], {type: 'text/plain'})
    element.href = URL.createObjectURL(file)
    element.download = `${filename}_extracted.txt`
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  return (
    <div ref={appRef} className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white">

      {/* hero section starts here */}
      <section className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-6xl md:text-8xl font-bold text-white mb-6 leading-tight">
            Secure Your Privacy,<br />
            <span className="bg-gradient-to-r from-green-400 to-blue-400 bg-clip-text text-transparent">
              Clean Your Files
            </span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto leading-relaxed">
            AI-powered tool that identifies and removes personal information from your documents,
            ensuring your data stays private and secure.
          </p>
      {/* acertinity component is here  */}
          <div className="mt-6 text-3xl md:text-5xl font-extrabold">
            <GsapTextFlip
            />
          </div>

          <button
            onClick={() => document.getElementById('upload-section').scrollIntoView({ behavior: 'smooth' })}
            className="bg-green-500 hover:bg-green-600 text-white font-bold py-4 mt-9 px-8 rounded-full transition-all duration-300 ease-in-out transform hover:scale-105 shadow-lg hover:shadow-xl hover:shadow-green-500/60 relative z-10"
            style={{ fontSize: '18px', fontWeight: '700' }}
            onMouseEnter={(e) => {
              gsap.to(e.currentTarget, {
                duration: 0.3,
                scale: 1.05,
                boxShadow: '0 20px 25px -5px rgba(16, 185, 129, 0.4), 0 8px 10px -6px rgba(16, 185, 129, 0.2)',
                ease: 'power2.out'
              });
            }}
            onMouseLeave={(e) => {
              gsap.to(e.currentTarget, {
                duration: 0.3,
                scale: 1,
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
                ease: 'power2.out'
              });
            }}
          >
            Start Cleaning Files
          </button>
        </div>
      </section>

      <section id="upload-section" className="py-20 px-4">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-12 text-white">Upload Your Document</h2>

          <div
            className={`w-120 mx-auto p-8 rounded-3xl border border-white/15 transition-all duration-500 ease-cubic-bezier(0.25,0.1,0.25,1) ${
              uploadState === 'uploading' ? 'scale-110' : 'scale-100'
            } ${dragActive ? 'border-green-500 bg-green-500/10 scale-110' : 'bg-white/5 hover:bg-white/10'}`}
            style={{ width: '480px', borderRadius: '20px' }}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            ref={(el) => {
              if (el) {
                gsap.from(el, {
                  scrollTrigger: {
                    trigger: el,
                    start: 'top 80%'
                  },
                  duration: 0.8,
                  opacity: 0,
                  y: 30,
                  ease: 'power2.out'
                });
              }
            }}
          >
            {uploadState === 'idle' && (
              <>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx,.xlsx,.xls,.jpg,.jpeg,.png,.tiff,.bmp"
                  onChange={handleInputChange}
                  className="hidden"
                  id="fileInput"
                />
                <label htmlFor="fileInput" className="cursor-pointer block text-center">
                  <div className="text-6xl mb-6"></div>
                  <h3 className="text-2xl font-semibold mb-4 text-white">Drop your file here</h3>
                  <p className="text-gray-300 mb-6">or click to browse</p>
                  <div className="text-sm text-gray-400">PDF, Word, Excel, Images</div>
                </label>
              </>
            )}

            {uploadState === 'uploading' && (
              <div className="text-center">
                <div className="text-6xl mb-6 animate-pulse"></div>
                <h3 className="text-2xl font-semibold mb-6 text-white">Processing your file...</h3>
                <div className="w-full bg-gray-700 rounded-full h-4 mb-4">
                  <div
                    className="bg-gradient-to-r from-cyan-400 to-blue-500 h-4 rounded-full progress-stripe transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            )}

            {uploadState === 'success' && (
              <div className="text-center animate-fade-in">
                <div className="mb-6">
                  <svg width="64" height="64" viewBox="0 0 24 24" fill="none" className="mx-auto opacity-0 animate-[fadeIn_250ms_ease-in-out_250ms_forwards]">
                    <circle cx="12" cy="12" r="10" stroke="#4ADE80" strokeWidth="2"/>
                    <path d="M9 12l2 2 4-4" stroke="#4ADE80" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <h3 className="text-2xl font-semibold mb-4 text-white">File Cleaned Successfully!</h3>
                <p className="text-gray-300 mb-8">Your document has been processed and all personal information has been safely removed.</p>
                <div className="space-y-4">
                  {result?.redacted_file_url && (
                    <a
                      href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${result.redacted_file_url}`}
                      download={result.redacted_filename}
                      className="w-full block bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-300 text-center"
                    >
                      Download Clean File
                    </a>
                  )}
                  <button
                    onClick={resetUpload}
                    className="w-full border border-white/20 hover:border-white/40 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-300"
                  >
                    Process Another File
                  </button>
                </div>
              </div>
            )}

            {uploadState === 'error' && (
              <div className="text-center">
                <div className="text-6xl mb-6 text-red-500"></div>
                <h3 className="text-2xl font-semibold mb-4 text-white">Processing Failed</h3>
                <p className="text-red-300 mb-8">{error}</p>
                <button
                  onClick={resetUpload}
                  className="w-full bg-red-500 hover:bg-red-600 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-300"
                >
                  Try Again
                </button>
              </div>
            )}
          </div>

          {file && uploadState === 'idle' && (
            <div className="mt-6 p-4 bg-white/10 rounded-xl border border-white/20" style={{ width: '480px', margin: '24px auto' }}>
              <div className="flex justify-between items-center mb-4">
                <div>
                  <div className="text-white font-medium">{file.name}</div>
                  <div className="text-gray-400 text-sm">{(file.size / 1024 / 1024).toFixed(1)} MB</div>
                </div>
              </div>
              <button
                onClick={handleUpload}
                className="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-300"
              >
                Process File
              </button>
            </div>
          )}
        </div>
      </section>

{/* results section starts here */}
      {showResults && result && (
        <section className="py-20 px-4" ref={(el) => {
          if (el) {
            gsap.from(el, {
              scrollTrigger: {
                trigger: el,
                start: 'top 80%'
              },
              duration: 0.8,
              opacity: 0,
              y: 30,
              ease: 'power2.out'
            });
          }
        }}>
          <div className="max-w-4xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-12 text-white">Processing Results</h2>

            {/* Stats Cards */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
              <div className="bg-white/10 p-6 rounded-xl border border-white/20">
                <div className="text-4xl mb-4"></div>
                <div className="text-gray-300 text-sm">File</div>
                <div className="text-white font-semibold">{result.filename}</div>
              </div>

              {result.confidence !== undefined && (
                <div className="bg-white/10 p-6 rounded-xl border border-white/20">
                  <div className="text-4xl mb-4"></div>
                  <div className="text-gray-300 text-sm">Confidence</div>
                  <div className="text-white font-semibold">{result.confidence}%</div>
                </div>
              )}

              <div className="bg-white/10 p-6 rounded-xl border border-white/20">
                <div className="text-4xl mb-4"></div>
                <div className="text-gray-300 text-sm">Type</div>
                <div className="text-white font-semibold">{result.file_type}</div>
              </div>

              {(result.total_entities !== undefined || result.total_pii_count !== undefined) && (
                <div className="bg-white/10 p-6 rounded-xl border border-white/20">
                  <div className="text-4xl mb-4"></div>
                  <div className="text-gray-300 text-sm">PII Found</div>
                  <div className="text-white font-semibold">
                    {result.total_entities || result.total_pii_count || 0} items
                  </div>
                </div>
              )}
            </div>

            {/* PII Summary */}
            {((result.pii_summary && Object.keys(result.pii_summary).length > 0) ||
              (result.entity_types && Object.keys(result.entity_types).length > 0)) && (
              <div className="bg-white/10 p-6 rounded-xl border border-white/20 mb-8">
                <h3 className="text-2xl font-semibold mb-6 text-white">PII Detection Summary</h3>
                <div className="flex flex-wrap gap-3 mb-6">
                  {/* Handle Excel format (pii_summary) */}
                  {result.pii_summary && Object.entries(result.pii_summary).map(([type, count]) => (
                    <div key={type} className="bg-green-500/20 text-green-300 px-4 py-2 rounded-lg border border-green-500/30">
                      <span className="font-medium capitalize">{type.replace('_', ' ')}</span>
                      <span className="ml-2 bg-green-500/30 px-2 py-1 rounded text-sm">{count}</span>
                    </div>
                  ))}
                  {/* Handle PDF/Word format (entity_types) */}
                  {result.entity_types && Object.entries(result.entity_types).map(([type, count]) => (
                    <div key={type} className="bg-green-500/20 text-green-300 px-4 py-2 rounded-lg border border-green-500/30">
                      <span className="font-medium capitalize">{type.replace('_', ' ')}</span>
                      <span className="ml-2 bg-green-500/30 px-2 py-1 rounded text-sm">{count}</span>
                    </div>
                  ))}
                </div>

                {/* Additional processing info */}
                {result.worksheets && result.worksheets.length > 0 && (
                  <div className="text-gray-300 text-sm mb-2">
                    <strong>Worksheets processed:</strong> {result.worksheets.join(', ')}
                  </div>
                )}

                {result.pages_processed !== undefined && (
                  <div className="text-gray-300 text-sm mb-2">
                    <strong>Pages processed:</strong> {result.pages_processed}
                  </div>
                )}
              </div>
            )}

            {/* Masked Text section  */}
            {result.masked_text && (
              <div className="bg-white/10 rounded-xl border border-white/20 overflow-hidden">
                <div className="p-6 border-b border-white/20 flex justify-between items-center">
                  <h3 className="text-2xl font-semibold text-white">Extracted Text</h3>
                  <div className="flex gap-3">
                    <button
                      onClick={() => copyToClipboard(result.masked_text)}
                      className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg transition-colors duration-300 flex items-center gap-2"
                    >
                       Copy
                    </button>
                    <button
                      onClick={() => downloadText(result.masked_text, result.filename)}
                      className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg transition-colors duration-300 flex items-center gap-2"
                    >
                       Download
                    </button>
                  </div>
                </div>
                <div className="p-6 font-mono text-sm text-gray-300 max-h-96 overflow-y-auto bg-black/30">
                  {result.masked_text || 'No text found in the document'}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Features Section */}
      <section className="py-20 px-4" ref={featuresRef}>
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16 text-white">Why Choose Our Privacy Tool?</h2>
          <div ref={(el) => {
            if (el) {
              gsap.from(el, {
                scrollTrigger: {
                  trigger: el,
                  start: 'top 80%'
                },
                duration: 0.8,
                opacity: 0,
                y: 30,
                ease: 'power2.out'
              });
            }
          }}>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                title: 'Advanced PII Detection',
                description: 'AI-powered recognition of names, addresses, phone numbers, emails, and sensitive data across multiple file formats.'
              },
              {
                title: 'Lightning Fast Processing',
                description: 'Process documents in seconds with our optimized algorithms while maintaining perfect accuracy.'
              },
              {
                title: 'Complete Data Security',
                description: 'Your files are processed locally and securely. No data is stored or transmitted to external servers.'
              },
              {
                title: 'Multiple File Formats',
                description: 'Support for PDF, Word documents, Excel spreadsheets, and common image formats.'
              }
            ].map((feature, index) => (
              <div
                key={index}
                className="feature-card p-6 bg-white/5 rounded-xl border border-white/10 hover:border-white/20 transition-all duration-400 opacity-0 translate-y-5 group"
                onMouseEnter={(e) => {
                  gsap.to(e.currentTarget, {
                    duration: 0.3,
                    y: -5,
                    boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.2), 0 8px 10px -6px rgba(0, 0, 0, 0.2)',
                    ease: 'power2.out'
                  });
                }}
                onMouseLeave={(e) => {
                  gsap.to(e.currentTarget, {
                    duration: 0.3,
                    y: 0,
                    boxShadow: 'none',
                    ease: 'power2.out'
                  });
                }}
              >
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold mb-4 text-white">{feature.title}</h3>
                <p className="text-gray-300 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
          </div>
        </div>
      </section>

      <section className="py-16 px-4" ref={badgesRef}>
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-wrap justify-center gap-8">
            {[
              { icon: '', text: '256-bit Encryption' },
              { icon: '', text: 'GDPR Compliant' },
              { icon: '', text: 'SOC 2 Certified' },
              { icon: '', text: 'Zero Data Retention' }
            ].map((badge, index) => (
              <div
                key={index}
                className="security-badge flex items-center space-x-3 px-6 py-3 bg-white/10 rounded-full border border-white/20 opacity-80 hover:opacity-100 transition-opacity duration-1000"
                style={{ animation: 'glowPulse 2.5s ease-in-out infinite' }}
              >
                <span className="text-2xl">{badge.icon}</span>
                <span className="text-white font-medium">{badge.text}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="bg-gray-900 py-8 px-4" style={{ backgroundColor: '#111111' }}>
        <div className="max-w-6xl mx-auto text-center">
          <p className="font-mono text-gray-400 text-sm">Privacy by Design</p>
        </div>
      </footer>
    </div>
  )
}

export default App
