import { useEffect, useState, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Loader2, Network } from 'lucide-react';
import { client } from '../api';

export default function CitationGraph({ 
  graphData: externalGraphData, 
  paperId,
  onNodeClick, 
  nodeColor = (node) => node.group === 'main' ? '#0284c7' : '#8b5cf6',
  nodeLabel = "name"
}) {
  const [internalData, setInternalData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(!externalGraphData);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef(null);
  const fgRef = useRef();

  const graphData = externalGraphData || internalData;

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

  // Backward compatibility fetch
  useEffect(() => {
    if (externalGraphData || !paperId) return;

    const fetchGraph = async () => {
      try {
        const data = await client.get(`/papers/${paperId}/graph`);
        if (data) setInternalData(data);
      } catch (err) {
        console.error("Failed to fetch graph:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchGraph();
  }, [paperId, externalGraphData]);

  // Ensure graph fits on load
  useEffect(() => {
    if (fgRef.current && graphData?.nodes?.length > 0) {
      setTimeout(() => {
        fgRef.current.zoomToFit(400, 50);
      }, 500);
    }
  }, [graphData]);

  if (loading) {
    return (
      <div className="p-16 text-center text-slate-500 flex flex-col items-center justify-center h-[600px] bg-slate-50/50 rounded-xl">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500 mb-3" />
        Loading graph visualization...
      </div>
    );
  }

  if (!graphData || graphData.nodes.length <= 1) {
    return (
      <div className="p-16 text-center text-slate-500 border-dashed border-2 rounded-xl flex flex-col items-center justify-center border-slate-200 h-[600px]">
        <Network className="w-8 h-8 text-slate-300 mb-2" />
        No citation network found for this paper.
      </div>
    );
  }

  return (
    <div ref={containerRef} className="rounded-xl overflow-hidden w-full h-[600px] bg-slate-50/50">
      <ForceGraph2D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeLabel={nodeLabel}
        nodeColor={nodeColor}
        onNodeClick={onNodeClick}
        nodeRelSize={6}
        linkDirectionalArrowLength={3.5}
        linkDirectionalArrowRelPos={1}
        linkColor={() => '#cbd5e1'}
      />
    </div>
  );
}
