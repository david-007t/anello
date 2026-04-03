'use client'

import { useState, useEffect } from 'react'
import { SplineScene } from './splite'
import { motion, AnimatePresence } from 'framer-motion'

type Position = 'top' | 'bottom' | 'hidden'

export function CornerMascot() {
  const [hovered, setHovered] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [position, setPosition] = useState<Position>('top')

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 2000)
    return () => clearTimeout(t)
  }, [])

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY
      const windowHeight = window.innerHeight
      const docHeight = document.documentElement.scrollHeight
      const nearBottom = scrollY + windowHeight >= docHeight - 200

      if (scrollY < 100) {
        setPosition('top')
      } else if (nearBottom) {
        setPosition('bottom')
      } else {
        setPosition('hidden')
      }
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    handleScroll()
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  if (!mounted) return null

  const positionClass =
    position === 'top'
      ? 'top-6 right-6'
      : position === 'bottom'
      ? 'bottom-6 right-6'
      : 'bottom-6 right-6'

  return (
    <AnimatePresence>
      {position !== 'hidden' && (
        <motion.div
          key={position}
          className={`fixed ${positionClass} z-50 cursor-pointer`}
          initial={{ opacity: 0, scale: 0.8, y: position === 'top' ? -20 : 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.8 }}
          transition={{ type: 'spring', stiffness: 200, damping: 20 }}
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
        >
          <motion.div
            animate={{ width: hovered ? 220 : 140, height: hovered ? 220 : 140 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            className="relative overflow-hidden"
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
      )}
    </AnimatePresence>
  )
}
