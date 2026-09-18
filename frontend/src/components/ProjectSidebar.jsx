import React, { useState, useEffect, useCallback } from 'react';
import { listProjects, getProject, createProject, deleteProject } from '../api';

export default function ProjectSidebar({
  isOpen,
  onClose,
  onSelectGeneration,
  currentScriptId,
}) {
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [generations, setGenerations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [showCreateInput, setShowCreateInput] = useState(false);

  const loadProjects = useCallback(async () => {
    try {
      setLoading(true);
      const projs = await listProjects();
      setProjects(projs);
      if (projs.length > 0 && !selectedProjectId) {
        setSelectedProjectId(projs[0].id);
      }
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedProjectId]);

  useEffect(() => {
    if (isOpen) {
      loadProjects();
    }
  }, [isOpen, loadProjects]);

  useEffect(() => {
    if (!selectedProjectId) return;
    async function loadGenerations() {
      try {
        const data = await getProject(selectedProjectId);
        setGenerations(data.generations || []);
      } catch (err) {
        console.error('Failed to fetch project designs:', err);
      }
    }
    loadGenerations();
  }, [selectedProjectId]);

  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    try {
      const proj = await createProject(newProjectName.trim());
      setNewProjectName('');
      setShowCreateInput(false);
      await loadProjects();
      setSelectedProjectId(proj.id);
    } catch (err) {
      console.error('Error creating project:', err);
    }
  };

  const handleDeleteProject = async (projId, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this workspace?')) return;
    try {
      await deleteProject(projId);
      if (selectedProjectId === projId) {
        setSelectedProjectId(null);
        setGenerations([]);
      }
      await loadProjects();
    } catch (err) {
      console.error('Error deleting project:', err);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        bottom: 0,
        width: '360px',
        backgroundColor: '#F6F6F0',
        borderRight: '1px solid rgba(71, 64, 64, 0.15)',
        boxShadow: '8px 0 28px rgba(71, 64, 64, 0.12)',
        zIndex: 5000,
        display: 'flex',
        flexDirection: 'column',
        color: '#474040',
        fontFamily: 'var(--font-sans)',
        animation: 'slideInLeft 0.22s ease-out',
      }}
    >
      {/* Atelier Header */}
      <div
        style={{
          padding: '16px 20px',
          background: '#474040',
          borderBottom: '1px solid rgba(255, 253, 226, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '16px' }}>📁</span>
          <h3
            style={{
              margin: 0,
              fontFamily: 'var(--font-serif)',
              fontSize: '17px',
              fontWeight: 500,
              fontStyle: 'italic',
              color: '#FFFDE2',
            }}
          >
            Atelier Workspaces
          </h3>
        </div>
        <button
          type="button"
          onClick={onClose}
          style={{
            background: 'rgba(255, 253, 226, 0.1)',
            border: '1px solid rgba(255, 253, 226, 0.2)',
            borderRadius: '4px',
            color: '#FFFDE2',
            cursor: 'pointer',
            fontSize: '12px',
            padding: '4px 8px',
          }}
        >
          ✕
        </button>
      </div>

      {/* Workspace Selector */}
      <div style={{ padding: '14px 18px', borderBottom: '1px solid rgba(71, 64, 64, 0.1)', background: '#EBEBE1' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '11px', fontWeight: 600, color: '#6B6363', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Workspaces
          </span>
          <button
            type="button"
            onClick={() => setShowCreateInput(!showCreateInput)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#474040',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              textDecoration: 'underline',
            }}
          >
            {showCreateInput ? 'Cancel' : '+ New Workspace'}
          </button>
        </div>

        {showCreateInput && (
          <form onSubmit={handleCreateProject} style={{ display: 'flex', gap: '6px', marginBottom: '10px' }}>
            <input
              type="text"
              placeholder="Workspace name..."
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              autoFocus
              style={{
                flex: 1,
                padding: '6px 10px',
                background: '#FFFFFF',
                border: '1px solid rgba(71, 64, 64, 0.2)',
                borderRadius: '5px',
                color: '#474040',
                fontSize: '12px',
                outline: 'none',
              }}
            />
            <button
              type="submit"
              style={{
                padding: '6px 10px',
                background: '#474040',
                border: 'none',
                borderRadius: '5px',
                color: '#FFFDE2',
                fontWeight: 600,
                fontSize: '11px',
                cursor: 'pointer',
              }}
            >
              Add
            </button>
          </form>
        )}

        {/* Folders */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {projects.map((proj) => (
            <div
              key={proj.id}
              onClick={() => setSelectedProjectId(proj.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '7px 10px',
                borderRadius: '6px',
                background: selectedProjectId === proj.id ? '#FFFFFF' : 'transparent',
                border: selectedProjectId === proj.id ? '1px solid rgba(71, 64, 64, 0.18)' : '1px solid transparent',
                cursor: 'pointer',
                boxShadow: selectedProjectId === proj.id ? '0 1px 4px rgba(71, 64, 64, 0.06)' : 'none',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                <span style={{ fontSize: '13px' }}>📂</span>
                <span style={{ fontSize: '12px', fontWeight: selectedProjectId === proj.id ? 600 : 500, color: '#474040', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                  {proj.name}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '10px', color: '#6B6363', background: '#E8E5DD', padding: '2px 5px', borderRadius: '4px', fontFamily: 'var(--font-mono)' }}>
                  {proj.generation_count}
                </span>
                {projects.length > 1 && (
                  <button
                    type="button"
                    onClick={(e) => handleDeleteProject(proj.id, e)}
                    title="Delete workspace"
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#99908F',
                      fontSize: '11px',
                      cursor: 'pointer',
                      padding: '2px',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.color = '#DC2626')}
                    onMouseLeave={(e) => (e.currentTarget.style.color = '#99908F')}
                  >
                    ✕
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Designs List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '14px 18px' }}>
        <div style={{ fontSize: '11px', fontWeight: 600, color: '#6B6363', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '10px' }}>
          Saved Models ({generations.length})
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {generations.map((gen) => {
            const isCurrent = gen.script_id === currentScriptId;
            return (
              <div
                key={gen.id}
                onClick={() => onSelectGeneration(gen.id)}
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: isCurrent ? '#FFFFFF' : '#FFFFFF',
                  border: isCurrent ? '2px solid #474040' : '1px solid rgba(71, 64, 64, 0.12)',
                  cursor: 'pointer',
                  boxShadow: '0 1px 4px rgba(71, 64, 64, 0.04)',
                  transition: 'border-color 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  if (!isCurrent) e.currentTarget.style.borderColor = '#474040';
                }}
                onMouseLeave={(e) => {
                  if (!isCurrent) e.currentTarget.style.borderColor = 'rgba(71, 64, 64, 0.12)';
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '12px', fontWeight: 700, color: '#474040' }}>
                    {gen.part_name || 'Parametric Part'}
                  </span>
                  <span style={{ fontSize: '10px', color: '#6B6363', fontFamily: 'var(--font-mono)' }}>
                    {gen.script_id}
                  </span>
                </div>
                <p style={{ margin: '4px 0 6px', fontSize: '11px', color: '#6B6363', lineHeight: 1.4, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {gen.prompt}
                </p>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '10px', color: '#99908F' }}>
                  <span>{gen.model_used || 'Gemini'}</span>
                  <span>{gen.created_at ? new Date(gen.created_at).toLocaleDateString() : ''}</span>
                </div>
              </div>
            );
          })}

          {generations.length === 0 && !loading && (
            <div style={{ textAlign: 'center', padding: '30px 12px', color: '#99908F', fontSize: '12px' }}>
              <div style={{ fontSize: '20px', marginBottom: '6px' }}>📐</div>
              Generated parts will be automatically saved here.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
