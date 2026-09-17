import { useEffect, useState, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Loader2, Network } from 'lucide-react';

export default function CitationGraph({ paperId }) {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef(null);

  useEffect(() => {
    // Update dimensions on window resize or mount
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: 600
        });
      }
    };
    
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/v1/papers/${paperId}/graph`);
        if (res.ok) {
          const data = await res.json();
          setGraphData(data);
        }
      } catch (err) {
        console.error("Failed to fetch graph:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchGraph();
  }, [paperId]);

  if (loading) {
    return (
      <div className="p-16 text-center text-slate-500 flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500 mb-3" />
        Loading graph visualization...
      </div>
    );
  }

  if (graphData.nodes.length <= 1) {
    return (
      <div className="p-16 text-center text-slate-500 border-dashed border-2 rounded-xl flex flex-col items-center justify-center border-slate-200">
        <Network className="w-8 h-8 text-slate-300 mb-2" />
        No citation network found for this paper.
      </div>
    );
  }

  return (
    <div ref={containerRef} className="rounded-xl overflow-hidden w-full bg-slate-50/50">
      <ForceGraph2D
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeLabel="name"
        nodeColor={node => node.group === 'main' ? '#0284c7' : '#8b5cf6'} // brand-600 and violet-500
        nodeRelSize={6}
        linkDirectionalArrowLength={3.5}
        linkDirectionalArrowRelPos={1}
        linkColor={() => '#cbd5e1'}
      />
    </div>
  );
}
