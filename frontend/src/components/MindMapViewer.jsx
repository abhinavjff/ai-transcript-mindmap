import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

const MindMapViewer = ({ mermaidCode }) => {
  const ref = useRef(null);

  useEffect(() => {
    if (mermaidCode && ref.current) {
      // 1. Initialize Mermaid
      mermaid.initialize({
        startOnLoad: true,
        theme: 'default',
        securityLevel: 'loose',
      });

      // 2. Clear previous render
      ref.current.removeAttribute('data-processed');
      ref.current.innerHTML = mermaidCode;

      // 3. Render the new diagram
      mermaid
        .run({
          nodes: [ref.current],
        })
        .catch((err) => console.error('Mermaid Render Error:', err));
    }
  }, [mermaidCode]);

  return (
    <div className="mermaid-container p-4 border rounded bg-white overflow-auto shadow-sm">
      <div className="mermaid" ref={ref}>
        {mermaidCode}
      </div>
    </div>
  );
};

export default MindMapViewer;
