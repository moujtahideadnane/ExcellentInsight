"use client"

import { useEffect } from 'react'

export default function CursorIntelligence() {
  useEffect(() => {
    // Only run on client
    if (typeof window === 'undefined') return

    // Only enable for desktop (fine-grained pointer)
    const isTouchDevice = !window.matchMedia('(pointer: fine)').matches
    if (isTouchDevice) return

    const cursor = document.createElement('div')
    cursor.className = 'gemini-cursor'
    document.body.appendChild(cursor)

    let mouseX = 0, mouseY = 0
    let cursorX = 0, cursorY = 0
    let animationFrameId: number

    const handleMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX
      mouseY = e.clientY
    }

    // Magnetic lag — cursor follows with inertia
    const animateCursor = () => {
      cursorX += (mouseX - cursorX) * 0.12
      cursorY += (mouseY - cursorY) * 0.12
      cursor.style.transform = `translate(${cursorX}px, ${cursorY}px)`
      animationFrameId = requestAnimationFrame(animateCursor)
    }

    document.addEventListener('mousemove', handleMouseMove)
    animateCursor()

    // Mutation observer to handle dynamically added elements
    const handleMouseOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (
        target.tagName.toLowerCase() === 'a' ||
        target.tagName.toLowerCase() === 'button' ||
        target.closest('a') ||
        target.closest('button') ||
        target.hasAttribute('data-cursor') ||
        target.closest('[data-cursor]')
      ) {
        cursor.classList.add('is-hovering')
      }
    }

    const handleMouseOut = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (
        target.tagName.toLowerCase() === 'a' ||
        target.tagName.toLowerCase() === 'button' ||
        target.closest('a') ||
        target.closest('button') ||
        target.hasAttribute('data-cursor') ||
        target.closest('[data-cursor]')
      ) {
        cursor.classList.remove('is-hovering')
      }
    }

    document.addEventListener('mouseover', handleMouseOver)
    document.addEventListener('mouseout', handleMouseOut)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseover', handleMouseOver)
      document.removeEventListener('mouseout', handleMouseOut)
      cancelAnimationFrame(animationFrameId)
      if (document.body.contains(cursor)) {
        document.body.removeChild(cursor)
      }
    }
  }, [])

  return null
}
