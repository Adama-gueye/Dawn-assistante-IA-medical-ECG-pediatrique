import React, { useMemo } from 'react';

export default function Particles({ count = 14 }) {
  const particles = useMemo(() => (
    Array.from({ length: count }, (_, i) => ({
      key: i,
      size: Math.random() * 4 + 2,
      left: Math.random() * 100,
      duration: Math.random() * 15 + 10,
      delay: Math.random() * 10,
    }))
  ), [count]);

  return (
    <>
      {particles.map((p) => (
        <div
          key={p.key}
          className="particle"
          style={{
            width: p.size, height: p.size, left: p.left + '%',
            animationDuration: p.duration + 's', animationDelay: p.delay + 's',
          }}
        />
      ))}
    </>
  );
}
