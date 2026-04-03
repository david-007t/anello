'use client'

import { useState, useEffect } from 'react'
import { SplineScene } from './splite'
import { motion, AnimatePresence } from 'framer-motion'

export function CornerMascot() {
  const [hovered, setHovered] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    // Delay mount so it doesn't block initial page load
    const t = setTimeout(() => setMounted(true), 2000)
    return () => clearTimeout(t)
  }, [])

  if (!mounted) return null

  return (
    <AnimatePresence>
      <motion.div
        className="fixed bottom-6 right-6 z-50 cursor-pointer"
        initial={{ opacity: 0, scale: 0.8, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        <motion.div
          animate={{ width: hovered ? 220 : 120, height: hovered ? 220 : 120 }}
          transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          className="relative rounded-2xl overflow-hidden bg-black/60 border border-white/10 backdrop-blur-md shadow-2xl"
          style={{ willChange: 'width, height' }}
        >
          <SplineScene
            scene="https://prod.spline.design/kZDDjO5HuC9GJUM2/scene.splinecode"
            className="w-full h-full"
          />
          <AnimatePresence>
            {hovered && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                className="absolute bottom-0 left-0 right-0 px-3 py-2 bg-gradient-to-t from-black/80 to-transparent"
              >
                <p className="text-white text-xs text-center font-medium">Hey, I&apos;m Anelo</p>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
