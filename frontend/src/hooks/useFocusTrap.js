import { useEffect, useRef } from 'react';

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

function getFocusableElements(container) {
  return Array.from(container.querySelectorAll(FOCUSABLE_SELECTOR));
}

/**
 * useFocusTrap — keeps keyboard Tab / Shift+Tab cycling inside a container
 * while `active` is true, and returns focus to the element that triggered
 * the modal when deactivated.
 *
 * Escape handling is intentionally left to each modal (already implemented
 * per-modal) — this hook only traps Tab navigation.
 */
export function useFocusTrap(containerRef, active) {
  const triggerRef = useRef(null);

  useEffect(() => {
    if (!active) return undefined;
    const container = containerRef.current;
    if (!container) return undefined;

    // Remember the trigger so focus can be restored on close.
    triggerRef.current = document.activeElement;

    // Move initial focus inside the modal (first focusable element).
    const initial = getFocusableElements(container);
    if (initial.length > 0 && !container.contains(document.activeElement)) {
      initial[0].focus({ preventScroll: true });
    }

    const handleKeyDown = (event) => {
      if (event.key !== 'Tab') return;
      const elements = getFocusableElements(container);
      if (elements.length === 0) {
        event.preventDefault();
        return;
      }
      const first = elements[0];
      const last = elements[elements.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      const trigger = triggerRef.current;
      if (trigger && typeof trigger.focus === 'function') {
        trigger.focus({ preventScroll: true });
      }
    };
  }, [active, containerRef]);
}

export default useFocusTrap;
