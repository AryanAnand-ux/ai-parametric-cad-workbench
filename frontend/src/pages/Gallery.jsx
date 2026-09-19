import React, { useState, useEffect, useCallback } from 'react';
import { getGallery, likeDesign, forkDesign } from '../api';

const SORT_OPTIONS = [
  { value: 'recent', label: 'Most Recent' },
  { value: 'popular', label: 'Most Liked' },
  { value: 'most_forked', label: 'Most Forked' },
];

const FEATURED_TAGS = ['bracket', 'enclosure', 'heatsink', 'gear', 'housing', 'flange', 'manifold', 'fixture'];

function DesignCard({ item, onFork, onLike, onLoad }) {
  const [liked, setLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(item.like_count || 0);
  const [forking, setForking] = useState(false);

  const handleLike = async (e) => {
    e.stopPropagation();
    if (liked) return;
    try {
      const res = await likeDesign(item.id);
      setLikeCount(res.like_count);
      setLiked(true);
    } catch {/* ignore */}
  };

  const handleFork = async (e) => {
    e.stopPropagation();
    setForking(true);
    try {
      const res = await forkDesign(item.id);
      onFork?.(res);
    } catch {/* ignore */} finally {
      setForking(false);
    }
  };

  const dims = item.mesh_info?.dimensions_mm || {};
  const dimStr = dims.x ? `${dims.x?.toFixed(0)}×${dims.y?.toFixed(0)}×${dims.z?.toFixed(0)} mm` : null;

  return (
    <div
      style={{
        background: '#FFFFFF',
        border: '1px solid rgba(71, 64, 64, 0.14)',
        borderRadius: '10px',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        transition: 'box-shadow 0.2s ease, transform 0.2s ease',
        cursor: 'pointer',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.boxShadow = '0 8px 28px rgba(71,64,64,0.14)';
        e.currentTarget.style.transform = 'translateY(-2px)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.boxShadow = 'none';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      {/* Preview thumbnail */}
      <div
        style={{
          height: '160px',
          background: 'linear-gradient(135deg, #EBEBE1 0%, #F6F6F0 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          flexShrink: 0,
        }}
      >
        {item.mesh_url ? (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '40px', marginBottom: '6px' }}>⬡</div>
            <div style={{ fontSize: '10px', color: '#99908F', fontFamily: 'var(--font-mono)', letterSpacing: '0.05em' }}>
              3D SOLID
            </div>
          </div>
        ) : (
          <div style={{ fontSize: '36px', opacity: 0.3 }}>◻</div>
        )}

        {/* Tag pills */}
        {item.tags?.length > 0 && (
          <div style={{ position: 'absolute', top: '8px', left: '8px', display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
            {item.tags.slice(0, 2).map(tag => (
              <span key={tag} style={{
                background: 'rgba(71,64,64,0.75)',
                color: '#FFFDE2',
                fontSize: '9px',
                fontWeight: 600,
                padding: '2px 7px',
                borderRadius: '12px',
                fontFamily: 'var(--font-mono)',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}>{tag}</span>
            ))}
          </div>
        )}

        {/* Fork badge */}
        {item.forked_from && (
          <div style={{
            position: 'absolute', top: '8px', right: '8px',
            background: 'rgba(72,146,53,0.85)',
            color: '#fff', fontSize: '9px', fontWeight: 700,
            padding: '2px 7px', borderRadius: '12px', fontFamily: 'var(--font-mono)',
          }}>FORK</div>
        )}
      </div>

      {/* Card body */}
      <div style={{ padding: '14px 16px', flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div>
          <div style={{
            fontSize: '13px', fontWeight: 600,
            color: '#474040', fontFamily: 'var(--font-sans)',
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          }}>
            {item.part_name}
          </div>
          <div style={{
            fontSize: '11px', color: '#99908F', marginTop: '2px',
            display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
            overflow: 'hidden', lineHeight: 1.5,
          }}>
            {item.description || item.prompt}
          </div>
        </div>

        {/* Metadata */}
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {dimStr && (
            <span style={{ fontSize: '10px', color: '#6B6363', fontFamily: 'var(--font-mono)' }}>
              📐 {dimStr}
            </span>
          )}
          {item.parameter_count > 0 && (
            <span style={{ fontSize: '10px', color: '#6B6363', fontFamily: 'var(--font-mono)' }}>
              🎛 {item.parameter_count}p
            </span>
          )}
          {item.mesh_info?.is_watertight && (
            <span style={{ fontSize: '10px', color: '#489235', fontFamily: 'var(--font-mono)' }}>
              ✓ watertight
            </span>
          )}
        </div>

        {/* Author & date */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 'auto', paddingTop: '8px', borderTop: '1px solid #EBEBE1' }}>
          <span style={{ fontSize: '11px', color: '#6B6363', fontFamily: 'var(--font-sans)' }}>
            by <strong style={{ color: '#474040' }}>{item.author}</strong>
          </span>
          <span style={{ fontSize: '10px', color: '#99908F', fontFamily: 'var(--font-mono)' }}>
            {new Date(item.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div style={{
        display: 'flex',
        borderTop: '1px solid #EBEBE1',
      }}>
        <button
          onClick={handleLike}
          style={{
            flex: 1, padding: '10px 0',
            background: liked ? '#F6F6F0' : 'transparent',
            border: 'none', borderRight: '1px solid #EBEBE1',
            cursor: liked ? 'default' : 'pointer',
            fontSize: '12px', color: liked ? '#489235' : '#6B6363',
            fontFamily: 'var(--font-sans)', fontWeight: 500,
            transition: 'all 0.15s ease',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px',
          }}
        >
          <span>{liked ? '♥' : '♡'}</span>
          <span>{likeCount}</span>
        </button>
        <button
          onClick={handleFork}
          disabled={forking}
          style={{
            flex: 1, padding: '10px 0',
            background: 'transparent', border: 'none',
            cursor: forking ? 'wait' : 'pointer',
            fontSize: '12px', color: '#474040',
            fontFamily: 'var(--font-sans)', fontWeight: 600,
            transition: 'all 0.15s ease',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px',
          }}
          onMouseEnter={e => !forking && (e.currentTarget.style.background = '#F6F6F0')}
          onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
        >
          <span>⑂</span>
          <span>{forking ? 'Forking…' : `Fork (${item.fork_count || 0})`}</span>
        </button>
      </div>
    </div>
  );
}

export default function Gallery({ onGoToApp }) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [activeTag, setActiveTag] = useState('');
  const [sortBy, setSortBy] = useState('recent');
  const [loading, setLoading] = useState(false);
  const [forkMessage, setForkMessage] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getGallery({ page, search, tag: activeTag, sortBy });
      setItems(res.items || []);
      setTotal(res.total || 0);
      setPages(res.pages || 1);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [page, search, activeTag, sortBy]);

  useEffect(() => { load(); }, [load]);

  const handleSearch = (e) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  const handleFork = (res) => {
    setForkMessage(`✓ Forked as "${res.part_name}" — open Workspaces to edit it.`);
    setTimeout(() => setForkMessage(null), 5000);
  };

  return (
    <div style={{ minHeight: '100vh', background: '#F6F6F0', fontFamily: 'var(--font-sans)' }}>

      {/* Header */}
      <div style={{ background: '#474040', padding: '0 40px', display: 'flex', alignItems: 'center', height: '64px', gap: '20px' }}>
        <button
          onClick={() => window.location.hash = ''}
          style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px', padding: 0 }}
        >
          <div style={{ width: '30px', height: '30px', background: '#FFFDE2', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#474040' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            </svg>
          </div>
          <span style={{ fontFamily: 'var(--font-serif)', fontSize: '18px', fontStyle: 'italic', color: '#FFFDE2', fontWeight: 500 }}>
            The CAD Atelier
          </span>
        </button>

        <span style={{ color: 'rgba(255,253,226,0.35)', fontSize: '18px' }}>·</span>
        <span style={{ fontFamily: 'var(--font-serif)', fontSize: '16px', fontStyle: 'italic', color: 'rgba(255,253,226,0.7)' }}>
          Community Gallery
        </span>

        <div style={{ flex: 1 }} />

        <button
          onClick={onGoToApp}
          style={{
            background: '#FFFDE2', color: '#474040', border: 'none',
            borderRadius: '6px', padding: '7px 16px', fontWeight: 600,
            fontSize: '12px', cursor: 'pointer', fontFamily: 'var(--font-sans)',
          }}
        >
          Open Workbench →
        </button>
      </div>

      {/* Hero */}
      <div style={{ background: '#474040', padding: '32px 40px 40px', textAlign: 'center' }}>
        <h1 style={{
          fontFamily: 'var(--font-serif)', fontSize: '32px', fontStyle: 'italic',
          color: '#FFFDE2', fontWeight: 500, margin: '0 0 8px',
        }}>
          Community CAD Gallery
        </h1>
        <p style={{ color: 'rgba(255,253,226,0.65)', fontSize: '14px', margin: '0 0 24px', fontFamily: 'var(--font-sans)' }}>
          Explore public parametric CAD designs. Fork any model to instantly load it into your workspace.
        </p>

        {/* Search bar */}
        <form onSubmit={handleSearch} style={{ maxWidth: '520px', margin: '0 auto', display: 'flex', gap: '8px' }}>
          <input
            type="text"
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            placeholder="Search brackets, heatsinks, gears…"
            style={{
              flex: 1, padding: '10px 16px',
              background: 'rgba(255,253,226,0.1)',
              border: '1px solid rgba(255,253,226,0.25)',
              borderRadius: '8px', color: '#FFFDE2', fontSize: '13px',
              fontFamily: 'var(--font-sans)', outline: 'none',
            }}
          />
          <button
            type="submit"
            style={{
              padding: '10px 20px', background: '#FFFDE2', border: 'none',
              borderRadius: '8px', color: '#474040', fontWeight: 700,
              fontSize: '13px', cursor: 'pointer', fontFamily: 'var(--font-sans)',
            }}
          >
            Search
          </button>
        </form>
      </div>

      {/* Fork success banner */}
      {forkMessage && (
        <div style={{
          background: '#489235', color: '#fff', padding: '12px 40px',
          fontSize: '13px', fontFamily: 'var(--font-sans)', fontWeight: 600,
          display: 'flex', alignItems: 'center', gap: '10px',
        }}>
          <span>{forkMessage}</span>
          <button
            onClick={onGoToApp}
            style={{ background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: '5px', color: '#fff', padding: '4px 12px', cursor: 'pointer', fontWeight: 700, fontSize: '12px' }}
          >
            Open Workbench
          </button>
        </div>
      )}

      {/* Filters */}
      <div style={{ padding: '20px 40px', display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap', borderBottom: '1px solid rgba(71,64,64,0.1)' }}>
        {/* Tag pills */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', flex: 1 }}>
          <button
            onClick={() => { setActiveTag(''); setPage(1); }}
            style={{
              padding: '5px 12px', borderRadius: '20px', fontSize: '11px', fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
              background: !activeTag ? '#474040' : 'transparent',
              color: !activeTag ? '#FFFDE2' : '#6B6363',
              border: !activeTag ? '1px solid #474040' : '1px solid rgba(71,64,64,0.2)',
            }}
          >All</button>
          {FEATURED_TAGS.map(tag => (
            <button
              key={tag}
              onClick={() => { setActiveTag(tag === activeTag ? '' : tag); setPage(1); }}
              style={{
                padding: '5px 12px', borderRadius: '20px', fontSize: '11px', fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                background: tag === activeTag ? '#474040' : 'transparent',
                color: tag === activeTag ? '#FFFDE2' : '#6B6363',
                border: tag === activeTag ? '1px solid #474040' : '1px solid rgba(71,64,64,0.2)',
                textTransform: 'capitalize',
              }}
            >{tag}</button>
          ))}
        </div>

        {/* Sort */}
        <select
          value={sortBy}
          onChange={e => { setSortBy(e.target.value); setPage(1); }}
          style={{
            padding: '7px 12px', border: '1px solid rgba(71,64,64,0.2)', borderRadius: '6px',
            background: '#fff', color: '#474040', fontSize: '12px', fontFamily: 'var(--font-sans)',
            cursor: 'pointer', outline: 'none',
          }}
        >
          {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>

        <span style={{ fontSize: '12px', color: '#99908F', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
          {total} designs
        </span>
      </div>

      {/* Grid */}
      <div style={{ padding: '32px 40px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '80px 0', color: '#99908F', fontFamily: 'var(--font-sans)' }}>
            <div style={{ fontSize: '32px', marginBottom: '12px', opacity: 0.4 }}>⬡</div>
            <div>Loading designs…</div>
          </div>
        ) : items.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '80px 0' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.2 }}>◻</div>
            <div style={{ fontSize: '16px', color: '#6B6363', fontFamily: 'var(--font-serif)', fontStyle: 'italic', marginBottom: '8px' }}>
              No designs published yet
            </div>
            <div style={{ fontSize: '13px', color: '#99908F', fontFamily: 'var(--font-sans)', marginBottom: '20px' }}>
              Generate a model in the workbench and publish it to the community.
            </div>
            <button
              onClick={onGoToApp}
              style={{
                background: '#474040', color: '#FFFDE2', border: 'none',
                borderRadius: '8px', padding: '10px 24px', fontSize: '13px',
                fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
              }}
            >
              Open Workbench →
            </button>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
            gap: '20px',
          }}>
            {items.map(item => (
              <DesignCard key={item.id} item={item} onFork={handleFork} />
            ))}
          </div>
        )}

        {/* Pagination */}
        {pages > 1 && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '40px' }}>
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              style={{
                padding: '8px 18px', borderRadius: '6px', border: '1px solid rgba(71,64,64,0.2)',
                background: page === 1 ? '#F6F6F0' : '#fff', color: '#474040',
                cursor: page === 1 ? 'default' : 'pointer', fontSize: '12px',
                fontFamily: 'var(--font-sans)', opacity: page === 1 ? 0.5 : 1,
              }}
            >← Prev</button>
            <span style={{ padding: '8px 14px', fontSize: '12px', color: '#6B6363', fontFamily: 'var(--font-mono)' }}>
              {page} / {pages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(pages, p + 1))}
              disabled={page === pages}
              style={{
                padding: '8px 18px', borderRadius: '6px', border: '1px solid rgba(71,64,64,0.2)',
                background: page === pages ? '#F6F6F0' : '#fff', color: '#474040',
                cursor: page === pages ? 'default' : 'pointer', fontSize: '12px',
                fontFamily: 'var(--font-sans)', opacity: page === pages ? 0.5 : 1,
              }}
            >Next →</button>
          </div>
        )}
      </div>
    </div>
  );
}
