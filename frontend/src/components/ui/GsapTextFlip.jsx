"use client";
import React, { useState, useEffect, useRef } from "react";
import { gsap } from "gsap";

export const GsapTextFlip = ({
  text = " placeholder for now ",
  words = ["safer", "cleaner", "private", "secure"],
  duration = 3
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const textRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    // Initial animation
    if (containerRef.current) {
      gsap.from(containerRef.current, {
        opacity: 0,
        y: 20,
        duration: 0.8,
        ease: "power2.out"
      });
    }
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => (prevIndex + 1) % words.length);
    }, duration * 1000);

    return () => clearInterval(interval);
  }, [duration, words.length]);

  useEffect(() => {
    if (textRef.current) {
      // Animate out
      gsap.to(textRef.current, {
        opacity: 0,
        y: -20,
        duration: 0.3,
        ease: "power2.in",
        onComplete: () => {
          // Animate in
          gsap.fromTo(
            textRef.current,
            { opacity: 0, y: 20 },
            {
              opacity: 1,
              y: 0,
              duration: 0.5,
              ease: "back.out(1.7)"
            }
          );
        }
      });
    }
  }, [currentIndex]);

  return (
    <div ref={containerRef} className="flex flex-col items-center">
      <span className="text-2xl font-bold tracking-tight md:text-4xl">
        {text}
      </span>
      <span
        ref={textRef}
        className="relative w-fit overflow-hidden rounded-md border border-transparent bg-white px-4 py-2 font-sans text-2xl font-bold tracking-tight text-black shadow-sm ring shadow-black/10 ring-black/10 md:text-4xl dark:bg-neutral-900 dark:text-white dark:shadow-sm dark:ring-1 dark:shadow-white/10 dark:ring-white/10"
      >
        {words[currentIndex]}
      </span>
    </div>
  );
};

export default GsapTextFlip;