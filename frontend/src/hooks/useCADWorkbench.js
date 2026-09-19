import { useReducer, useCallback, useRef } from 'react';

function getPersistedModel() {
  try {
    return JSON.parse(localStorage.getItem('cad_last_model') || 'null') || {};
  } catch {
    return {};
  }
}

const _p = getPersistedModel();

const initialState = {
  prompt: '',
  loading: false,
  recomputing: false,
  error: null,

  // Response state from /api/generate & /api/modify
  scriptId: _p.scriptId ?? null,
  partName: _p.partName ?? null,
  description: _p.description ?? null,
  pythonCode: _p.pythonCode ?? null,
  parameters: _p.parameters ?? [],
  parameterSearch: '',
  paramValues: _p.paramValues ?? {},
  meshUrl: _p.meshUrl ?? null,
  stepUrl: _p.stepUrl ?? null,
  objUrl: _p.objUrl ?? null,
  glbUrl: _p.glbUrl ?? null,
  meshInfo: _p.meshInfo ?? null,
  recompTime: null,
  modelUsed: null,
  designMode: _p.designMode ?? 'single_solid',
  components: _p.components ?? null,
  backendStatus: 'checking',

  // Sidebar navigation
  activeTab: 'all',

  // Chat-to-Modify state
  chatHistory: [],
  modifyPrompt: '',
  modifying: false,

  // Undo history
  modelHistory: [],

  // Viewport Control States
  showAxes: true,
  showGrid: true,
  materialType: 'cad_gray',
  visualStyle: 'shaded_edges',
  backgroundTheme: 'atelier_sand',
  cursorCoords: { x: '0.0', y: '0.0', z: '0.0' },
  activeCamView: 'iso',
  showDimensions: true,

  // Modals
  showCodeModal: false,
  showAuthModal: false,
  showProjectSidebar: false,
  showShareModal: false,
  showOnboarding: false,

  // Stream progress
  streamPhase: 'rag_retrieval',
  streamProgress: 0,
  streamMessage: '',
  streamAttempts: 0,
};

function cadWorkbenchReducer(state, action) {
  switch (action.type) {
    case 'SET_FIELD':
      return { ...state, [action.field]: action.value };

    case 'SET_FIELDS':
      return { ...state, ...action.fields };

    case 'SET_ERROR':
      return { ...state, error: action.error };

    case 'DISMISS_ERROR':
      return { ...state, error: null };

    case 'APPLY_PART_RESPONSE': {
      const res = action.payload;
      const initialValues = {};
      (res.parameters || []).forEach((p) => {
        initialValues[p.name] = p.default;
      });

      // Save to localStorage
      try {
        localStorage.setItem(
          'cad_last_model',
          JSON.stringify({
            scriptId: res.script_id,
            partName: res.part_name,
            description: res.description,
            pythonCode: res.python_code,
            parameters: res.parameters || [],
            paramValues: initialValues,
            meshUrl: res.mesh_url,
            stepUrl: res.step_url,
            objUrl: res.obj_url,
            glbUrl: res.glb_url,
            meshInfo: res.mesh_info || {},
            designMode: res.design_mode || 'single_solid',
            components: res.components || null,
          })
        );
      } catch (e) {
        console.warn('[Persist] Could not save model to localStorage:', e);
      }

      return {
        ...state,
        scriptId: res.script_id,
        partName: res.part_name,
        description: res.description,
        pythonCode: res.python_code,
        parameters: res.parameters || [],
        parameterSearch: '',
        paramValues: initialValues,
        meshUrl: res.mesh_url,
        stepUrl: res.step_url,
        objUrl: res.obj_url ?? null,
        glbUrl: res.glb_url ?? null,
        meshInfo: res.mesh_info || {},
        recompTime: res.recomputation_time_ms,
        modelUsed: res.model_used,
        designMode: res.design_mode || 'single_solid',
        components: res.components || null,
        activeTab: res.parameters && res.parameters.length > 0 ? 'sliders' : state.activeTab,
      };
    }

    case 'SET_RECOMPUTE_SUCCESS': {
      const res = action.payload;
      return {
        ...state,
        meshUrl: res.mesh_url,
        stepUrl: res.step_url,
        objUrl: res.obj_url ?? state.objUrl,
        glbUrl: res.glb_url ?? state.glbUrl,
        meshInfo: res.mesh_info || {},
        recompTime: res.recomputation_time_ms,
        error: null,
      };
    }

    case 'UPDATE_PARAM_VALUE':
      return {
        ...state,
        paramValues: {
          ...state.paramValues,
          [action.name]: action.value,
        },
      };

    case 'RESET_PARAMS': {
      const defaultValues = {};
      state.parameters.forEach((p) => {
        defaultValues[p.name] = p.default;
      });
      return {
        ...state,
        paramValues: defaultValues,
      };
    }

    case 'PUSH_SNAPSHOT': {
      if (!state.scriptId || !state.pythonCode) return state;
      const snapshot = {
        scriptId: state.scriptId,
        partName: state.partName,
        description: state.description,
        pythonCode: state.pythonCode,
        parameters: [...state.parameters],
        paramValues: { ...state.paramValues },
        meshUrl: state.meshUrl,
        stepUrl: state.stepUrl,
        objUrl: state.objUrl,
        glbUrl: state.glbUrl,
        meshInfo: state.meshInfo,
        recompTime: state.recompTime,
        modelUsed: state.modelUsed,
        designMode: state.designMode,
        components: state.components,
      };
      return {
        ...state,
        modelHistory: [snapshot, ...state.modelHistory].slice(0, 5),
      };
    }

    case 'POP_SNAPSHOT': {
      if (state.modelHistory.length === 0) return state;
      const [lastState, ...remaining] = state.modelHistory;
      return {
        ...state,
        modelHistory: remaining,
        scriptId: lastState.scriptId,
        partName: lastState.partName,
        description: lastState.description,
        pythonCode: lastState.pythonCode,
        parameters: lastState.parameters || [],
        paramValues: lastState.paramValues || {},
        meshUrl: lastState.meshUrl,
        stepUrl: lastState.stepUrl,
        objUrl: lastState.objUrl ?? null,
        glbUrl: lastState.glbUrl ?? null,
        meshInfo: lastState.meshInfo || {},
        recompTime: lastState.recompTime,
        modelUsed: lastState.modelUsed,
        designMode: lastState.designMode || 'single_solid',
        components: lastState.components || null,
      };
    }

    case 'ADD_CHAT_MESSAGE':
      return {
        ...state,
        chatHistory: [...state.chatHistory, action.message],
      };

    case 'UPDATE_STREAM':
      return {
        ...state,
        streamPhase: action.phase ?? state.streamPhase,
        streamProgress: action.progress ?? state.streamProgress,
        streamMessage: action.message ?? state.streamMessage,
        streamAttempts: action.attempts ?? state.streamAttempts,
      };

    default:
      return state;
  }
}

export function useCADWorkbench() {
  const [state, dispatch] = useReducer(cadWorkbenchReducer, initialState);
  const paramValuesRef = useRef(state.paramValues);
  paramValuesRef.current = state.paramValues;

  const setField = useCallback((field, value) => {
    dispatch({ type: 'SET_FIELD', field, value });
  }, []);

  const setFields = useCallback((fields) => {
    dispatch({ type: 'SET_FIELDS', fields });
  }, []);

  const setError = useCallback((error) => {
    dispatch({ type: 'SET_ERROR', error });
  }, []);

  const dismissError = useCallback(() => {
    dispatch({ type: 'DISMISS_ERROR' });
  }, []);

  const applyPartResponse = useCallback((payload) => {
    dispatch({ type: 'APPLY_PART_RESPONSE', payload });
  }, []);

  const setRecomputeSuccess = useCallback((payload) => {
    dispatch({ type: 'SET_RECOMPUTE_SUCCESS', payload });
  }, []);

  const updateParamValue = useCallback((name, value) => {
    dispatch({ type: 'UPDATE_PARAM_VALUE', name, value });
  }, []);

  const resetParams = useCallback(() => {
    dispatch({ type: 'RESET_PARAMS' });
  }, []);

  const pushSnapshot = useCallback(() => {
    dispatch({ type: 'PUSH_SNAPSHOT' });
  }, []);

  const popSnapshot = useCallback(() => {
    dispatch({ type: 'POP_SNAPSHOT' });
  }, []);

  const addChatMessage = useCallback((message) => {
    dispatch({ type: 'ADD_CHAT_MESSAGE', message });
  }, []);

  const updateStream = useCallback((data) => {
    dispatch({ type: 'UPDATE_STREAM', ...data });
  }, []);

  return {
    state,
    dispatch,
    paramValuesRef,
    setField,
    setFields,
    setError,
    dismissError,
    applyPartResponse,
    setRecomputeSuccess,
    updateParamValue,
    resetParams,
    pushSnapshot,
    popSnapshot,
    addChatMessage,
    updateStream,
    setPrompt: useCallback((v) => setField('prompt', v), [setField]),
    setActiveTab: useCallback((v) => setField('activeTab', v), [setField]),
    setParameterSearch: useCallback((v) => setField('parameterSearch', v), [setField]),
    setModifyPrompt: useCallback((v) => setField('modifyPrompt', v), [setField]),
    setModifying: useCallback((v) => setField('modifying', v), [setField]),
    setLoading: useCallback((v) => setField('loading', v), [setField]),
    setRecomputing: useCallback((v) => setField('recomputing', v), [setField]),
    setVisualStyle: useCallback((v) => setField('visualStyle', v), [setField]),
    setMaterialType: useCallback((v) => setField('materialType', v), [setField]),
    setBackgroundTheme: useCallback((v) => setField('backgroundTheme', v), [setField]),
    setShowAxes: useCallback((v) => setField('showAxes', typeof v === 'function' ? v(state.showAxes) : v), [setField, state.showAxes]),
    setShowGrid: useCallback((v) => setField('showGrid', typeof v === 'function' ? v(state.showGrid) : v), [setField, state.showGrid]),
    setShowDimensions: useCallback((v) => setField('showDimensions', typeof v === 'function' ? v(state.showDimensions) : v), [setField, state.showDimensions]),
    setCursorCoords: useCallback((v) => setField('cursorCoords', v), [setField]),
    setActiveCamView: useCallback((v) => setField('activeCamView', v), [setField]),
    setShowCodeModal: useCallback((v) => setField('showCodeModal', v), [setField]),
    setShowAuthModal: useCallback((v) => setField('showAuthModal', v), [setField]),
    setShowProjectSidebar: useCallback((v) => setField('showProjectSidebar', v), [setField]),
    setShowShareModal: useCallback((v) => setField('showShareModal', v), [setField]),
    setShowOnboarding: useCallback((v) => setField('showOnboarding', v), [setField]),
    setBackendStatus: useCallback((v) => setField('backendStatus', v), [setField]),
    setChatHistory: useCallback((fnOrVal) => {
      setField('chatHistory', typeof fnOrVal === 'function' ? fnOrVal(state.chatHistory) : fnOrVal);
    }, [setField, state.chatHistory]),
  };
}
