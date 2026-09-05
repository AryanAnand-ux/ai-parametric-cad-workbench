/**
 * LandingPage.jsx — The CAD Atelier
 *
 * Faithfully adapted from "The Studio by Julie Granger" (thestudiobyjuliegranger.com):
 *  - Warm sand / linen palette (#F6F6F0, #EBEBE1, #FFFFFF) with deep warm espresso contrast (#474040)
 *  - Editorial Newsreader serif typography with italicized accents & Open Sans body
 *  - Fixed translucent mega-nav with center brand mark, language selector, and pill CTA
 *  - Full-bleed atelier hero with warm golden hour tones, breadcrumbs, and floating video preview card
 *  - Expandable video lightbox modal
 *  - Three Pillars of the Method with circular numbered badges
 *  - Four vertical discipline cards with high-fashion editorial imagery (Aerospace, Kinematics, Thermal, Robotics)
 *  - Manifesto quote section with giant background letter watermark
 *  - "Is The Atelier For You?" three-card user matrix
 *  - On-Demand platform mockup showcase with dual desktop & mobile viewports
 *  - Live interactive parameter slider node with real-time volume & bounding box calculations
 *  - Engineering client testimonials
 *  - Three-tier membership & access pricing cards
 *  - Hairline accordion FAQ with smooth expand
 *  - Grand luxury footer with giant "BY CAD ATELIER" watermark and bottom craft panoramic banner
 */

import React, { useState, useEffect } from 'react';
import heroBg from './assets/julie_atelier_hero.jpg';
import bottomCraftBg from './assets/julie_craft_bottom.jpg';
import aeroImg from './assets/discipline_aerospace.jpg';
import kinematicsImg from './assets/discipline_kinematics.jpg';
import thermalImg from './assets/discipline_thermal.jpg';
import roboticsImg from './assets/discipline_robotics.jpg';

// Elegant SVG Icons
const Icons = {
  Play: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <polygon points="5 3 19 12 5 21 5 3" />
    </svg>
  ),
  Expand: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="15 3 21 3 21 9" />
      <polyline points="9 21 3 21 3 15" />
      <line x1="21" y1="3" x2="14" y2="10" />
      <line x1="3" y1="21" x2="10" y2="14" />
    </svg>
  ),
  Close: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ),
  ArrowRight: () => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="5" y1="12" x2="19" y2="12" />
      <polyline points="12 5 19 12 12 19" />
    </svg>
  ),
  Check: () => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  Cube: () => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
      <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
      <line x1="12" y1="22.08" x2="12" y2="12" />
    </svg>
  ),
  Sliders: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="4" y1="21" x2="4" y2="14" />
      <line x1="4" y1="10" x2="4" y2="3" />
      <line x1="12" y1="21" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12" y2="3" />
      <line x1="20" y1="21" x2="20" y2="16" />
      <line x1="20" y1="12" x2="20" y2="3" />
      <line x1="1" y1="14" x2="7" y2="14" />
      <line x1="9" y1="8" x2="15" y2="8" />
      <line x1="17" y1="16" x2="23" y2="16" />
    </svg>
  ),
};

export default function LandingPage({ onEnterApp }) {
  const [scrollY, setScrollY] = useState(0);
  const [videoModalOpen, setVideoModalOpen] = useState(false);
  const [language, setLanguage] = useState('EN');
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  // Interactive Live Sliders State (Embedded on Landing Page)
  const [demoSliders, setDemoSliders] = useState({
    width: 60,
    finCount: 12,
    finHeight: 28,
    wallThick: 3.5,
  });

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const calculatedVolume = (
    ((demoSliders.width * demoSliders.width * 8 +
      demoSliders.finCount * demoSliders.width * demoSliders.finHeight * demoSliders.wallThick) /
      1000)
  ).toFixed(1);

  const handleSubscribe = (e) => {
    e.preventDefault();
    if (email) {
      setSubscribed(true);
      setTimeout(() => setSubscribed(false), 4000);
      setEmail('');
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#F6F6F0',
      color: '#474040',
      fontFamily: '"Open Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      fontSize: '14px',
      lineHeight: '1.5',
      WebkitFontSmoothing: 'antialiased',
      overflowX: 'hidden',
    }}>


      {/* ── STICKY BOUTIQUE MEGA-NAV HEADER ─────────────────────────── */}
      <header style={{
        position: 'sticky',
        top: 0,
        zIndex: 900,
        height: '70px',
        backgroundColor: scrollY > 30 ? 'rgba(246, 246, 240, 0.85)' : 'rgba(71, 64, 64, 0.35)',
        backdropFilter: 'blur(20px) saturate(180%)',
        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
        borderBottom: scrollY > 30 ? '1px solid rgba(71, 64, 64, 0.1)' : '1px solid rgba(255, 253, 226, 0.12)',
        boxShadow: scrollY > 30 ? '0 2px 20px rgba(71, 64, 64, 0.08)' : '0 2px 20px rgba(0, 0, 0, 0.15)',
        color: scrollY > 30 ? '#474040' : '#FFFDE2',
        transition: 'all 0.35s ease',
        display: 'flex',
        alignItems: 'center',
        padding: '0 clamp(16px, 4vw, 50px)',
      }}>
        <div style={{
          width: '100%',
          maxWidth: '1440px',
          margin: '0 auto',
          display: 'grid',
          gridTemplateColumns: '1fr auto 1fr',
          alignItems: 'center',
        }}>
          {/* Left Navigation Links */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: '28px' }}>
            {['Pillars', 'Disciplines', 'Platform', 'FAQ'].map((link) => (
              <a
                key={link}
                href={`#${link.toLowerCase().replace(/\s+/g, '-')}`}
                style={{
                  color: 'inherit',
                  textDecoration: 'none',
                  fontSize: '13px',
                  fontWeight: '500',
                  letterSpacing: '0.01em',
                  opacity: 0.9,
                  transition: 'opacity 0.2s ease',
                }}
                onMouseEnter={e => e.currentTarget.style.opacity = '1'}
                onMouseLeave={e => e.currentTarget.style.opacity = '0.9'}
              >
                {link}
              </a>
            ))}
          </nav>

          {/* Center Brand Logo (Julie Granger Signature Style) */}
          <div
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            style={{
              cursor: 'pointer',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              lineHeight: 1,
            }}
          >
            <span style={{
              fontFamily: '"Newsreader", Georgia, serif',
              fontSize: '22px',
              fontWeight: '400',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}>
              The CAD Atelier
            </span>
            <span style={{
              fontSize: '9px',
              letterSpacing: '0.22em',
              opacity: 0.75,
              textTransform: 'uppercase',
              marginTop: '4px',
            }}>
              Minor Project · 2025
            </span>
          </div>

          {/* Right Actions: Language + CTA */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '20px' }}>
            <div style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px', opacity: 0.85 }}>
              <span
                onClick={() => setLanguage('EN')}
                style={{ cursor: 'pointer', fontWeight: language === 'EN' ? '700' : '400' }}
              >
                EN
              </span>
              <span>/</span>
              <span
                onClick={() => setLanguage('FR')}
                style={{ cursor: 'pointer', fontWeight: language === 'FR' ? '700' : '400' }}
              >
                FR
              </span>
            </div>

            <button
              onClick={onEnterApp}
              style={{
                backgroundColor: scrollY > 30 ? '#474040' : 'rgba(71, 64, 64, 0.65)',
                color: '#FFFDE2',
                border: scrollY > 30 ? 'none' : '1px solid rgba(255, 253, 226, 0.7)',
                borderRadius: '8px',
                padding: '9px 18px',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                backdropFilter: 'blur(6px)',
                WebkitBackdropFilter: 'blur(6px)',
                transition: 'all 0.25s ease',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.backgroundColor = '#383232';
                e.currentTarget.style.transform = 'translateY(-1px)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.backgroundColor = scrollY > 30 ? '#474040' : 'rgba(71, 64, 64, 0.65)';
                e.currentTarget.style.transform = 'none';
              }}
            >
              <span>Launch Workbench</span>
              <Icons.ArrowRight />
            </button>
          </div>
        </div>
      </header>

      {/* ── HERO SECTION (Exact Julie Granger Layout & Atelier Tone) ── */}
      <section style={{
        position: 'relative',
        width: '100%',
        minHeight: 'calc(100vh - 70px)',
        display: 'flex',
        alignItems: 'flex-end',
        overflow: 'hidden',
        backgroundImage: `url(${heroBg})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center 35%',
      }}>
        {/* Soft Warm Editorial Tint Overlay */}
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundColor: 'rgba(71, 64, 64, 0.42)',
          zIndex: 1,
        }} />
        <div style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(to top, rgba(71, 64, 64, 0.8) 0%, rgba(71, 64, 64, 0.2) 60%, rgba(71, 64, 64, 0.4) 100%)',
          zIndex: 1,
        }} />

        <div style={{
          position: 'relative',
          zIndex: 2,
          width: '100%',
          maxWidth: '1440px',
          margin: '0 auto',
          padding: 'clamp(32px, 6vh, 64px) clamp(16px, 4vw, 50px)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          flexWrap: 'wrap',
          gap: '32px',
        }}>
          {/* Left Editorial Content */}
          <div style={{ maxWidth: '640px', color: '#FFFFFF' }}>
            {/* Soft Category Badge */}
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: 'rgba(255, 253, 226, 0.2)',
              border: '1px solid rgba(255, 253, 226, 0.4)',
              borderRadius: '4px',
              padding: '6px 12px',
              fontSize: '11px',
              fontWeight: '600',
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: '#FFFDE2',
              backdropFilter: 'blur(8px)',
              marginBottom: '24px',
            }}>
              <span>ACADEMIC MINOR PROJECT · OPENCASCADE &amp; BUILD123D</span>
            </div>

            {/* Newsreader Editorial Serif Title */}
            <h1 style={{
              fontFamily: '"Newsreader", Georgia, serif',
              fontSize: 'clamp(26px, 3.5vw, 46px)',
              fontWeight: '400',
              lineHeight: 1.1,
              margin: '0 0 16px',
              letterSpacing: '-0.015em',
              color: '#FFFFFF',
            }}>
              AI Parametric CAD Workbench,<br />
              <span style={{ fontStyle: 'italic', color: '#FFFDE2', opacity: 0.92 }}>
                crafted for generative mechanical design.
              </span>
            </h1>

            {/* Subtitle */}
            <p style={{
              fontSize: '14px',
              lineHeight: 1.65,
              color: 'rgba(255, 255, 255, 0.85)',
              maxWidth: '440px',
              margin: '0 0 28px',
            }}>
              An undergraduate engineering project pairing natural language generative AI with exact OpenCASCADE B-Rep geometry, real-time parametric recomputation, and interactive 3D WebGL rendering.
            </p>

            {/* Actions */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
              <button
                onClick={onEnterApp}
                style={{
                  backgroundColor: '#FFFDE2',
                  color: '#474040',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '14px 28px',
                  fontSize: '14px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.backgroundColor = '#FFFFFF';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.backgroundColor = '#FFFDE2';
                  e.currentTarget.style.transform = 'none';
                }}
              >
                <span>Launch Live Workbench</span>
                <Icons.ArrowRight />
              </button>

              <a
                href="#pillars"
                style={{
                  backgroundColor: 'rgba(255, 253, 226, 0.12)',
                  color: '#FFFDE2',
                  border: '1px solid rgba(255, 253, 226, 0.5)',
                  borderRadius: '6px',
                  padding: '14px 24px',
                  fontSize: '14px',
                  fontWeight: '500',
                  textDecoration: 'none',
                  display: 'inline-flex',
                  alignItems: 'center',
                  backdropFilter: 'blur(10px)',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={e => e.currentTarget.style.borderColor = '#FFFDE2'}
                onMouseLeave={e => e.currentTarget.style.borderColor = 'rgba(255, 253, 226, 0.5)'}
              >
                Explore Architecture
              </a>
            </div>
          </div>

          {/* Right Floating Video / 3D Card (Directly from Julie Granger reference screenshot!) */}
          <div style={{
            width: '320px',
            aspectRatio: '320/190',
            backgroundColor: 'rgba(71, 64, 64, 0.85)',
            border: '1px solid rgba(255, 253, 226, 0.3)',
            borderRadius: '20px',
            overflow: 'hidden',
            position: 'relative',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4)',
            backdropFilter: 'blur(10px)',
          }}>
            <img
              src={kinematicsImg}
              alt="Live CAD Engine Demonstration"
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                opacity: 0.9,
              }}
            />

            {/* Dark gradient overlay */}
            <div style={{
              position: 'absolute',
              inset: 0,
              background: 'linear-gradient(to top, rgba(71, 64, 64, 0.7) 0%, transparent 60%)',
            }} />

            {/* Label inside thumbnail */}
            <div style={{
              position: 'absolute',
              top: '12px',
              left: '14px',
              fontSize: '11px',
              fontWeight: '600',
              color: '#FFFDE2',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}>
              Project Demo &amp; Workbench Session
            </div>

            {/* Expand Lightbox Button (Exact icon & position from Julie Granger) */}
            <button
              onClick={() => setVideoModalOpen(true)}
              style={{
                position: 'absolute',
                right: '12px',
                bottom: '12px',
                width: '34px',
                height: '34px',
                borderRadius: '8px',
                backgroundColor: 'rgba(255, 253, 226, 0.85)',
                color: '#474040',
                border: '1px solid rgba(255, 253, 226, 0.9)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                boxShadow: '0 4px 12px rgba(71, 64, 64, 0.25)',
                transition: 'transform 0.2s ease',
              }}
              onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.08)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
              title="Expand Video"
            >
              <Icons.Expand />
            </button>
          </div>
        </div>
      </section>

      {/* ── PARTNER & CAD STANDARDS STRIP (.logos) ─────────────────── */}
      <section style={{
        backgroundColor: '#FFFFFF',
        borderBottom: '1px solid rgba(71, 64, 64, 0.1)',
        padding: '24px clamp(16px, 4vw, 50px)',
      }}>
        <div style={{
          maxWidth: '1440px',
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '24px',
          opacity: 0.65,
          fontFamily: '"Newsreader", Georgia, serif',
          fontSize: '15px',
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
        }}>
          <span>OPENCASCADE 7.8</span>
          <span>•</span>
          <span>BUILD123D SOLID ENGINE</span>
          <span>•</span>
          <span>ISO 10303 STEP AP214</span>
          <span>•</span>
          <span>THREE.JS WEBGL</span>
          <span>•</span>
          <span>GEMINI 2.5 PRO REASONING</span>
          <span>•</span>
          <span>FASTAPI ASYNC</span>
        </div>
      </section>

      {/* ── 3 PILLARS OF THE METHOD (.benefits) ─────────────────────── */}
      <section id="pillars" style={{
        padding: 'clamp(60px, 10vh, 110px) clamp(16px, 4vw, 50px)',
        maxWidth: '1440px',
        margin: '0 auto',
      }}>
        <div style={{ textAlign: 'center', maxWidth: '640px', margin: '0 auto 60px' }}>
          <div style={{
            fontSize: '12px',
            fontWeight: '600',
            letterSpacing: '0.14em',
            textTransform: 'uppercase',
            color: 'rgba(71, 64, 64, 0.6)',
            marginBottom: '12px',
          }}>
            Project Architecture &amp; Pillars
          </div>
          <h2 style={{
            fontFamily: '"Newsreader", Georgia, serif',
            fontSize: 'clamp(32px, 4vw, 44px)',
            fontWeight: '400',
            lineHeight: 1.1,
            margin: 0,
            color: '#474040',
          }}>
            Deterministic CAD kernels meet<br />
            <span style={{ fontStyle: 'italic' }}>generative artificial intelligence.</span>
          </h2>
        </div>

        {/* 3 Pillar Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '32px',
        }}>
          {[
            {
              num: '01',
              title: 'Watertight B-Rep Solid Engine',
              desc: 'Unlike polygonal mesh generators, our workbench produces pure OpenCASCADE boundary representation solids with exact topological faces, cylinders, fillets, and chamfers.',
              tag: 'Exact Solid Geometry',
            },
            {
              num: '02',
              title: 'Sub-140ms Parametric Sliders',
              desc: 'Automatically extracts critical variables into dynamic UI sliders. Adjusting parameters recomputes Python build123d geometry in real time without extra LLM token calls.',
              tag: 'Zero-Token Recompute',
            },
            {
              num: '03',
              title: 'Universal STEP & STL Export',
              desc: 'Seamless compatibility with Autodesk Fusion 360, SolidWorks, Siemens NX, and standard 3D slicers with native ISO 10303 STEP AP214 and STL export.',
              tag: 'Industry CAD Standard',
            },
          ].map((pillar) => (
            <div
              key={pillar.num}
              style={{
                backgroundColor: '#FFFFFF',
                border: '1px solid rgba(71, 64, 64, 0.1)',
                borderRadius: '16px',
                padding: '36px 30px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                boxShadow: '0 8px 24px rgba(71, 64, 64, 0.04)',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 16px 36px rgba(71, 64, 64, 0.08)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.transform = 'none';
                e.currentTarget.style.boxShadow = '0 8px 24px rgba(71, 64, 64, 0.04)';
              }}
            >
              <div>
                <div style={{
                  width: '46px',
                  height: '46px',
                  borderRadius: '50%',
                  backgroundColor: '#F6F6F0',
                  border: '1px solid rgba(71, 64, 64, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily: '"Newsreader", Georgia, serif',
                  fontSize: '18px',
                  fontWeight: '600',
                  color: '#474040',
                  marginBottom: '24px',
                }}>
                  {pillar.num}
                </div>
                <h3 style={{
                  fontFamily: '"Newsreader", Georgia, serif',
                  fontSize: '24px',
                  fontWeight: '400',
                  margin: '0 0 14px',
                  color: '#474040',
                }}>
                  {pillar.title}
                </h3>
                <p style={{
                  fontSize: '14px',
                  lineHeight: 1.65,
                  color: 'rgba(71, 64, 64, 0.75)',
                  margin: 0,
                }}>
                  {pillar.desc}
                </p>
              </div>

              <div style={{
                marginTop: '28px',
                paddingTop: '16px',
                borderTop: '1px solid rgba(71, 64, 64, 0.08)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <span style={{
                  fontSize: '11px',
                  fontWeight: '600',
                  color: '#474040',
                  letterSpacing: '0.06em',
                  textTransform: 'uppercase',
                }}>
                  {pillar.tag}
                </span>
                <span style={{ color: 'rgba(71, 64, 64, 0.4)' }}>→</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── DISCIPLINES SHOWCASE (.disciplines — 4 Tall Portrait Cards) ── */}
      <section id="disciplines" style={{
        backgroundColor: '#EBEBE1',
        padding: 'clamp(60px, 10vh, 110px) clamp(16px, 4vw, 50px)',
      }}>
        <div style={{ maxWidth: '1440px', margin: '0 auto' }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-end',
            marginBottom: '48px',
            flexWrap: 'wrap',
            gap: '20px',
          }}>
            <div>
              <div style={{
                fontSize: '12px',
                fontWeight: '600',
                letterSpacing: '0.14em',
                textTransform: 'uppercase',
                color: 'rgba(71, 64, 64, 0.6)',
                marginBottom: '10px',
              }}>
                Evaluation Domains
              </div>
              <h2 style={{
                fontFamily: '"Newsreader", Georgia, serif',
                fontSize: 'clamp(32px, 4vw, 44px)',
                fontWeight: '400',
                margin: 0,
                color: '#474040',
              }}>
                Demonstrated mechanical case studies.
              </h2>
            </div>

            <button
              onClick={onEnterApp}
              style={{
                backgroundColor: '#474040',
                color: '#FFFDE2',
                border: 'none',
                borderRadius: '6px',
                padding: '12px 22px',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span>Explore Part Libraries</span>
              <Icons.ArrowRight />
            </button>
          </div>

          {/* 4 Portrait Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '24px',
          }}>
            {[
              {
                id: 'aero',
                title: 'Aerospace & Propulsion',
                tag: 'TURBOPUMPS & IMPELLERS',
                img: aeroImg,
                desc: 'Centrifugal flow impellers, curved shroud blades, and rocket injector manifolds.',
              },
              {
                id: 'kin',
                title: 'Kinematics & Horology',
                tag: 'GEARTRAINS & BEARINGS',
                img: kinematicsImg,
                desc: 'Involute spur gears, sun-and-planet planetary gearboxes, and precision escapements.',
              },
              {
                id: 'therm',
                title: 'Thermal Architecture',
                tag: 'HEATSINKS & COLD PLATES',
                img: thermalImg,
                desc: 'Extruded pinned heatsinks, skived fins, and micro-channel liquid cold plate lids.',
              },
              {
                id: 'rob',
                title: 'Lightweight Robotics',
                tag: 'CHASSIS & DRONE ARMS',
                img: roboticsImg,
                desc: 'High-modulus carbon drone booms, cycloidal drive joints, and NEMA motor brackets.',
              },
            ].map((discipline) => (
              <div
                key={discipline.id}
                onClick={onEnterApp}
                style={{
                  backgroundColor: '#FFFFFF',
                  borderRadius: '16px',
                  overflow: 'hidden',
                  cursor: 'pointer',
                  border: '1px solid rgba(71, 64, 64, 0.1)',
                  boxShadow: '0 10px 28px rgba(71, 64, 64, 0.05)',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'all 0.35s cubic-bezier(0.2, 0.8, 0.2, 1)',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.transform = 'translateY(-8px)';
                  e.currentTarget.style.boxShadow = '0 20px 40px rgba(71, 64, 64, 0.14)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.transform = 'none';
                  e.currentTarget.style.boxShadow = '0 10px 28px rgba(71, 64, 64, 0.05)';
                }}
              >
                {/* 3:4 Aspect Image Frame */}
                <div style={{
                  position: 'relative',
                  width: '100%',
                  aspectRatio: '3/4',
                  overflow: 'hidden',
                  backgroundColor: '#F6F6F0',
                }}>
                  <img
                    src={discipline.img}
                    alt={discipline.title}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      transition: 'transform 0.5s ease',
                    }}
                    onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.05)'}
                    onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
                  />
                  <div style={{
                    position: 'absolute',
                    top: '14px',
                    left: '14px',
                    backgroundColor: 'rgba(255, 253, 226, 0.9)',
                    color: '#474040',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '10px',
                    fontWeight: '700',
                    letterSpacing: '0.08em',
                  }}>
                    {discipline.tag}
                  </div>
                </div>

                {/* Card Content */}
                <div style={{ padding: '24px 20px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <h3 style={{
                      fontFamily: '"Newsreader", Georgia, serif',
                      fontSize: '22px',
                      fontWeight: '400',
                      margin: '0 0 8px',
                      color: '#474040',
                    }}>
                      {discipline.title}
                    </h3>
                    <p style={{
                      fontSize: '13px',
                      lineHeight: 1.55,
                      color: 'rgba(71, 64, 64, 0.7)',
                      margin: 0,
                    }}>
                      {discipline.desc}
                    </p>
                  </div>

                  <div style={{
                    marginTop: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '12px',
                    fontWeight: '600',
                    color: '#474040',
                  }}>
                    <span>Inspect in Workbench</span>
                    <span>→</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── MANIFESTO STORY CALLOUT (.method-story with letter watermark) ── */}
      <section style={{
        position: 'relative',
        padding: 'clamp(80px, 12vh, 140px) clamp(16px, 4vw, 50px)',
        backgroundColor: '#F6F6F0',
        overflow: 'hidden',
        textAlign: 'center',
      }}>
        {/* Giant initial watermark "A" behind text */}
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          fontFamily: '"Newsreader", Georgia, serif',
          fontSize: 'clamp(280px, 35vw, 440px)',
          fontWeight: '400',
          color: 'rgba(71, 64, 64, 0.04)',
          userSelect: 'none',
          pointerEvents: 'none',
          lineHeight: 0.8,
          zIndex: 0,
        }}>
          A
        </div>

        <div style={{ position: 'relative', zIndex: 1, maxWidth: '820px', margin: '0 auto' }}>
          <div style={{
            fontSize: '12px',
            fontWeight: '600',
            letterSpacing: '0.14em',
            textTransform: 'uppercase',
            color: 'rgba(71, 64, 64, 0.55)',
            marginBottom: '20px',
          }}>
            Project Abstract &amp; Vision
          </div>

          <blockquote style={{
            fontFamily: '"Newsreader", Georgia, serif',
            fontSize: 'clamp(24px, 3.2vw, 38px)',
            fontWeight: '400',
            lineHeight: 1.35,
            color: '#474040',
            margin: '0 0 28px',
            fontStyle: 'italic',
          }}>
            “We designed this AI Parametric CAD Workbench to explore how generative AI can interface with precision engineering. By pairing large language models with deterministic B-Rep kernels, students and engineers can move from text prompts to verified 3D models seamlessly.”
          </blockquote>

          <div style={{
            fontSize: '13px',
            fontWeight: '600',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: '#474040',
          }}>
            Aryan Anand — Project Developer &amp; Researcher
          </div>
          <div style={{ fontSize: '12px', color: 'rgba(71, 64, 64, 0.6)', marginTop: '4px' }}>
            Academic Minor Project · OpenCASCADE &amp; build123d Generative Workbench
          </div>
        </div>
      </section>

      {/* ── "IS THE WORKBENCH FOR YOU?" GRID (.for-you) ─────────────── */}
      <section style={{
        padding: 'clamp(60px, 10vh, 100px) clamp(16px, 4vw, 50px)',
        maxWidth: '1440px',
        margin: '0 auto',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '50px' }}>
          <div style={{
            fontSize: '12px',
            fontWeight: '600',
            letterSpacing: '0.14em',
            textTransform: 'uppercase',
            color: 'rgba(71, 64, 64, 0.6)',
            marginBottom: '10px',
          }}>
            Application Scenarios
          </div>
          <h2 style={{
            fontFamily: '"Newsreader", Georgia, serif',
            fontSize: 'clamp(32px, 4vw, 42px)',
            fontWeight: '400',
            margin: 0,
            color: '#474040',
          }}>
            Built for students, researchers &amp; makers.
          </h2>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '28px',
        }}>
          {[
            {
              role: 'Engineering Students & Labs',
              headline: 'Rapid conceptual mechanical drafting.',
              body: 'Quickly generate reference CAD components and explore parametric variations for academic coursework, lab assignments, and rapid 3D printing prototyping.',
            },
            {
              role: 'CAD & Robotics Hobbyists',
              headline: 'Automate entire families of parts instantly.',
              body: 'Stop redrawing standard bearings, flanges, and mounts for different bolt circles. Our dual-output schema auto-generates dynamic UI sliders for every critical variable.',
            },
            {
              role: 'Academic & AI Researchers',
              headline: 'Benchmarking LLMs on solid modeling.',
              body: 'A comprehensive testbed demonstrating RAG-augmented code generation, AST execution sandboxing, and real-time WebGL rendering for AI-driven CAD research.',
            },
          ].map((item, idx) => (
            <div
              key={idx}
              style={{
                backgroundColor: '#FFFFFF',
                borderRadius: '16px',
                padding: '36px 32px',
                border: '1px solid rgba(71, 64, 64, 0.1)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                boxShadow: '0 6px 20px rgba(71, 64, 64, 0.04)',
              }}
            >
              <div>
                <span style={{
                  display: 'inline-block',
                  fontSize: '11px',
                  fontWeight: '700',
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: 'rgba(71, 64, 64, 0.6)',
                  marginBottom: '16px',
                }}>
                  {item.role}
                </span>
                <h3 style={{
                  fontFamily: '"Newsreader", Georgia, serif',
                  fontSize: '22px',
                  fontWeight: '400',
                  lineHeight: 1.25,
                  margin: '0 0 14px',
                  color: '#474040',
                }}>
                  {item.headline}
                </h3>
                <p style={{
                  fontSize: '14px',
                  lineHeight: 1.65,
                  color: 'rgba(71, 64, 64, 0.75)',
                  margin: 0,
                }}>
                  {item.body}
                </p>
              </div>

              <div style={{ marginTop: '28px' }}>
                <button
                  onClick={onEnterApp}
                  style={{
                    background: 'none',
                    border: 'none',
                    padding: 0,
                    fontSize: '13px',
                    fontWeight: '600',
                    color: '#474040',
                    textDecoration: 'underline',
                    textUnderlineOffset: '3px',
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  <span>Launch project demo</span>
                  <span>→</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Interactive sliders section removed per user request */}
      {false && <section id="interactive-sliders" style={{
        backgroundColor: '#EBEBE1',
        padding: 'clamp(60px, 10vh, 100px) clamp(16px, 4vw, 50px)',
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '40px' }}>
            <div style={{
              fontSize: '12px',
              fontWeight: '600',
              letterSpacing: '0.14em',
              textTransform: 'uppercase',
              color: 'rgba(71, 64, 64, 0.6)',
              marginBottom: '10px',
            }}>
              Live Algorithmic Kernel
            </div>
            <h2 style={{
              fontFamily: '"Newsreader", Georgia, serif',
              fontSize: 'clamp(32px, 4vw, 44px)',
              fontWeight: '400',
              margin: '0 0 14px',
              color: '#474040',
            }}>
              Test the recomputation engine in real-time.
            </h2>
            <p style={{
              fontSize: '15px',
              color: 'rgba(71, 64, 64, 0.75)',
              maxWidth: '600px',
              margin: '0 auto',
            }}>
              Drag the sliders below to watch volume and geometric boundary envelopes update instantly without LLM token re-queries.
            </p>
          </div>

          {/* Interactive Card */}
          <div style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '20px',
            border: '1px solid rgba(71, 64, 64, 0.12)',
            boxShadow: '0 16px 40px rgba(71, 64, 64, 0.08)',
            padding: ' clamp(24px, 4vw, 44px)',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '40px',
            alignItems: 'center',
          }}>
            {/* Sliders Column */}
            <div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                marginBottom: '28px',
                paddingBottom: '14px',
                borderBottom: '1px solid rgba(71, 64, 64, 0.1)',
              }}>
                <Icons.Sliders />
                <span style={{ fontSize: '15px', fontWeight: '700', color: '#474040' }}>
                  Extruded CPU Heatsink Parameters
                </span>
              </div>

              {/* Slider 1: Base Width */}
              <div style={{ marginBottom: '22px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '13px', fontWeight: '600', color: '#474040' }}>Base Width</span>
                  <span style={{ fontSize: '13px', fontFamily: '"JetBrains Mono", monospace', fontWeight: '700' }}>
                    {demoSliders.width} mm
                  </span>
                </div>
                <input
                  type="range"
                  min="30"
                  max="120"
                  value={demoSliders.width}
                  onChange={e => setDemoSliders({ ...demoSliders, width: Number(e.target.value) })}
                  style={{ width: '100%', accentColor: '#474040', cursor: 'pointer' }}
                />
              </div>

              {/* Slider 2: Fin Count */}
              <div style={{ marginBottom: '22px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '13px', fontWeight: '600', color: '#474040' }}>Fin Count</span>
                  <span style={{ fontSize: '13px', fontFamily: '"JetBrains Mono", monospace', fontWeight: '700' }}>
                    {demoSliders.finCount} fins
                  </span>
                </div>
                <input
                  type="range"
                  min="4"
                  max="24"
                  value={demoSliders.finCount}
                  onChange={e => setDemoSliders({ ...demoSliders, finCount: Number(e.target.value) })}
                  style={{ width: '100%', accentColor: '#474040', cursor: 'pointer' }}
                />
              </div>

              {/* Slider 3: Fin Height */}
              <div style={{ marginBottom: '22px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '13px', fontWeight: '600', color: '#474040' }}>Fin Height</span>
                  <span style={{ fontSize: '13px', fontFamily: '"JetBrains Mono", monospace', fontWeight: '700' }}>
                    {demoSliders.finHeight} mm
                  </span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="60"
                  value={demoSliders.finHeight}
                  onChange={e => setDemoSliders({ ...demoSliders, finHeight: Number(e.target.value) })}
                  style={{ width: '100%', accentColor: '#474040', cursor: 'pointer' }}
                />
              </div>

              {/* Slider 4: Wall Thickness */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '13px', fontWeight: '600', color: '#474040' }}>Wall Thickness</span>
                  <span style={{ fontSize: '13px', fontFamily: '"JetBrains Mono", monospace', fontWeight: '700' }}>
                    {demoSliders.wallThick} mm
                  </span>
                </div>
                <input
                  type="range"
                  min="1.0"
                  max="6.0"
                  step="0.5"
                  value={demoSliders.wallThick}
                  onChange={e => setDemoSliders({ ...demoSliders, wallThick: Number(e.target.value) })}
                  style={{ width: '100%', accentColor: '#474040', cursor: 'pointer' }}
                />
              </div>
            </div>

            {/* Computed Telemetry Column */}
            <div style={{
              backgroundColor: '#F6F6F0',
              borderRadius: '16px',
              padding: '30px',
              border: '1px solid rgba(71, 64, 64, 0.1)',
            }}>
              <div style={{
                fontSize: '11px',
                fontWeight: '700',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                color: 'rgba(71, 64, 64, 0.6)',
                marginBottom: '16px',
              }}>
                Live B-Rep Analytical Output
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
                <div style={{
                  backgroundColor: '#FFFFFF',
                  padding: '16px',
                  borderRadius: '10px',
                  border: '1px solid rgba(71, 64, 64, 0.08)',
                }}>
                  <div style={{ fontSize: '11px', color: 'rgba(71, 64, 64, 0.6)', marginBottom: '4px' }}>Solid Volume</div>
                  <div style={{
                    fontSize: '22px',
                    fontFamily: '"JetBrains Mono", monospace',
                    fontWeight: '700',
                    color: '#474040',
                  }}>
                    {calculatedVolume} <span style={{ fontSize: '14px', fontWeight: '400' }}>cm³</span>
                  </div>
                </div>

                <div style={{
                  backgroundColor: '#FFFFFF',
                  padding: '16px',
                  borderRadius: '10px',
                  border: '1px solid rgba(71, 64, 64, 0.08)',
                }}>
                  <div style={{ fontSize: '11px', color: 'rgba(71, 64, 64, 0.6)', marginBottom: '4px' }}>Recompute Speed</div>
                  <div style={{
                    fontSize: '22px',
                    fontFamily: '"JetBrains Mono", monospace',
                    fontWeight: '700',
                    color: '#489235',
                  }}>
                    &lt;128 <span style={{ fontSize: '14px', fontWeight: '400' }}>ms</span>
                  </div>
                </div>
              </div>

              <div style={{
                fontSize: '12px',
                color: 'rgba(71, 64, 64, 0.8)',
                lineHeight: 1.6,
                marginBottom: '24px',
              }}>
                ✓ 100% Manifold 2-manifold B-Rep topology<br />
                ✓ Dimension Envelope: {demoSliders.width} × {demoSliders.width} × {demoSliders.finHeight + 8} mm<br />
                ✓ Export Ready: AP214 STEP &amp; STL
              </div>

              <button
                onClick={onEnterApp}
                style={{
                  width: '100%',
                  backgroundColor: '#474040',
                  color: '#FFFDE2',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '12px 18px',
                  fontSize: '13px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  transition: 'background-color 0.2s ease',
                }}
                onMouseEnter={e => e.currentTarget.style.backgroundColor = '#383232'}
                onMouseLeave={e => e.currentTarget.style.backgroundColor = '#474040'}
              >
                <span>Open in 3D WebGL Studio</span>
                <Icons.ArrowRight />
              </button>
            </div>
          </div>
        </div>
      </section>}

      {/* Client reviews section removed per user request */}
      {false && <section style={{
        padding: 'clamp(60px, 10vh, 100px) clamp(16px, 4vw, 50px)',
        maxWidth: '1440px',
        margin: '0 auto',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '50px' }}>
          <div style={{
            fontSize: '12px',
            fontWeight: '600',
            letterSpacing: '0.14em',
            textTransform: 'uppercase',
            color: 'rgba(71, 64, 64, 0.6)',
            marginBottom: '10px',
          }}>
            Client Words
          </div>
          <h2 style={{
            fontFamily: '"Newsreader", Georgia, serif',
            fontSize: 'clamp(32px, 4vw, 42px)',
            fontWeight: '400',
            margin: 0,
            color: '#474040',
          }}>
            Adopted by hardware studios worldwide.
          </h2>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '28px',
        }}>
          {[
            {
              quote: '“AI CAD Workbench eliminated 90% of our repetitive bracket and heatsink drafting in Fusion 360. The dual-output sliders feel like magic.”',
              author: 'Dr. Marcus Vance',
              role: 'Head of Mechanical R&D, AeroDynamics Lab',
            },
            {
              quote: '“The fact that it generates real AP214 STEP files rather than messy polygonal STL meshes is an engineering triumph. Direct CNC import with zero errors.”',
              author: 'Claire Delacroix',
              role: 'Principal Horology Designer, Geneva Ateliers',
            },
            {
              quote: '“The sub-140ms slider recomputation makes generative CAD feel like a tactile physical instrument. Our team creates 5x more prototype variations.”',
              author: 'Siddharth Nair',
              role: 'Co-Founder & CTO, HyperLoop Systems',
            },
          ].map((rev, idx) => (
            <div
              key={idx}
              style={{
                backgroundColor: '#FFFFFF',
                borderRadius: '16px',
                padding: '36px 30px',
                border: '1px solid rgba(71, 64, 64, 0.1)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <p style={{
                fontFamily: '"Newsreader", Georgia, serif',
                fontSize: '18px',
                lineHeight: 1.5,
                color: '#474040',
                margin: '0 0 24px',
                fontStyle: 'italic',
              }}>
                {rev.quote}
              </p>
              <div>
                <div style={{ fontSize: '13px', fontWeight: '700', color: '#474040' }}>{rev.author}</div>
                <div style={{ fontSize: '11px', color: 'rgba(71, 64, 64, 0.6)', marginTop: '2px' }}>{rev.role}</div>
              </div>
            </div>
          ))}
        </div>
      </section>}

      {/* Pricing section removed per user request */}
      {false && <section id="pricing" style={{
        backgroundColor: '#EBEBE1',
        padding: 'clamp(60px, 10vh, 110px) clamp(16px, 4vw, 50px)',
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '50px' }}>
            <div style={{
              fontSize: '12px',
              fontWeight: '600',
              letterSpacing: '0.14em',
              textTransform: 'uppercase',
              color: 'rgba(71, 64, 64, 0.6)',
              marginBottom: '10px',
            }}>
              Atelier Memberships
            </div>
            <h2 style={{
              fontFamily: '"Newsreader", Georgia, serif',
              fontSize: 'clamp(32px, 4vw, 44px)',
              fontWeight: '400',
              margin: '0 0 12px',
              color: '#474040',
            }}>
              Transparent, subscription-free options.
            </h2>
            <p style={{ fontSize: '15px', color: 'rgba(71, 64, 64, 0.7)', margin: 0 }}>
              Start free with no credit card required. Upgrade anytime as your manufacturing volume scales.
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '28px',
          }}>
            {[
              {
                tier: 'Community Atelier',
                price: '$0',
                period: 'forever free',
                desc: 'Ideal for students, makers, and rapid hobbyist 3D printing exploration.',
                features: [
                  'Unlimited natural language prompts',
                  'Watertight STL mesh export',
                  'Live parameter sliders',
                  'ChromaDB 69-part RAG index',
                  'Community forum support',
                ],
                popular: false,
                buttonText: 'Get Started Free',
              },
              {
                tier: 'Professional Studio',
                price: '$49',
                period: 'per month',
                desc: 'For professional hardware engineers, aerospace designers, and CNC shops.',
                features: [
                  'Everything in Community',
                  'Production AP214 STEP solid downloads',
                  'Multi-model Gemini 2.5 Pro fallback',
                  'Conversational Chat-to-Modify versioning',
                  'Python source code inspector',
                  'Sub-140ms recomputation priority',
                ],
                popular: true,
                buttonText: 'Start 14-Day Trial',
              },
              {
                tier: 'Enterprise Atelier',
                price: 'Custom',
                period: 'bespoke engagement',
                desc: 'Dedicated on-premise Docker deployment with air-gapped security compliance.',
                features: [
                  'Everything in Professional',
                  'On-premise Docker & Nginx deployment',
                  'Custom proprietary RAG corpus indexing',
                  'AST sandbox policy customizations',
                  'Dedicated SLA & 1-on-1 engineer support',
                ],
                popular: false,
                buttonText: 'Contact Atelier Team',
              },
            ].map((plan, idx) => (
              <div
                key={idx}
                style={{
                  backgroundColor: '#FFFFFF',
                  borderRadius: '20px',
                  padding: '40px 32px',
                  border: plan.popular ? '2px solid #474040' : '1px solid rgba(71, 64, 64, 0.12)',
                  position: 'relative',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: plan.popular ? '0 16px 36px rgba(71, 64, 64, 0.12)' : '0 8px 24px rgba(71, 64, 64, 0.04)',
                }}
              >
                {plan.popular && (
                  <div style={{
                    position: 'absolute',
                    top: '-12px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    backgroundColor: '#474040',
                    color: '#FFFDE2',
                    padding: '4px 12px',
                    borderRadius: '20px',
                    fontSize: '10px',
                    fontWeight: '700',
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase',
                  }}>
                    Most Popular
                  </div>
                )}

                <div>
                  <h3 style={{
                    fontFamily: '"Newsreader", Georgia, serif',
                    fontSize: '24px',
                    fontWeight: '400',
                    margin: '0 0 8px',
                    color: '#474040',
                  }}>
                    {plan.tier}
                  </h3>
                  <div style={{
                    fontSize: '36px',
                    fontFamily: '"Newsreader", Georgia, serif',
                    fontWeight: '400',
                    color: '#474040',
                    margin: '16px 0 4px',
                  }}>
                    {plan.price}
                    <span style={{ fontSize: '13px', fontFamily: '"Open Sans", sans-serif', color: 'rgba(71, 64, 64, 0.6)', marginLeft: '6px' }}>
                      / {plan.period}
                    </span>
                  </div>
                  <p style={{ fontSize: '13px', lineHeight: 1.6, color: 'rgba(71, 64, 64, 0.7)', margin: '0 0 24px' }}>
                    {plan.desc}
                  </p>

                  <div style={{ borderTop: '1px solid rgba(71, 64, 64, 0.1)', paddingTop: '20px', marginBottom: '28px' }}>
                    <div style={{ fontSize: '11px', fontWeight: '700', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(71, 64, 64, 0.5)', marginBottom: '14px' }}>
                      Included in Plan:
                    </div>
                    {plan.features.map((feat, fIdx) => (
                      <div key={fIdx} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', marginBottom: '10px', fontSize: '13px', color: 'rgba(71, 64, 64, 0.85)' }}>
                        <span style={{ color: '#474040', marginTop: '2px' }}><Icons.Check /></span>
                        <span>{feat}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  onClick={onEnterApp}
                  style={{
                    width: '100%',
                    backgroundColor: plan.popular ? '#474040' : 'transparent',
                    color: plan.popular ? '#FFFDE2' : '#474040',
                    border: plan.popular ? 'none' : '1px solid rgba(71, 64, 64, 0.35)',
                    borderRadius: '8px',
                    padding: '12px 18px',
                    fontSize: '13px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.backgroundColor = '#474040';
                    e.currentTarget.style.color = '#FFFDE2';
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.backgroundColor = plan.popular ? '#474040' : 'transparent';
                    e.currentTarget.style.color = plan.popular ? '#FFFDE2' : '#474040';
                  }}
                >
                  {plan.buttonText}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>}

      {/* ── HAIRLINE ACCORDION FAQ (.faq) ───────────────────────────── */}
      <section id="faq" style={{
        padding: 'clamp(60px, 10vh, 100px) clamp(16px, 4vw, 50px)',
        maxWidth: '960px',
        margin: '0 auto',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '50px' }}>
          <div style={{
            fontSize: '12px',
            fontWeight: '600',
            letterSpacing: '0.14em',
            textTransform: 'uppercase',
            color: 'rgba(71, 64, 64, 0.6)',
            marginBottom: '10px',
          }}>
            Inquiries &amp; Technical Detail
          </div>
          <h2 style={{
            fontFamily: '"Newsreader", Georgia, serif',
            fontSize: 'clamp(32px, 4vw, 42px)',
            fontWeight: '400',
            margin: 0,
            color: '#474040',
          }}>
            Frequently Asked Questions
          </h2>
        </div>

        <div>
          {[
            {
              q: 'What is the objective of this academic minor project?',
              a: 'This project demonstrates the integration of Generative AI (LLMs) with deterministic CAD engineering kernels. Rather than generating low-quality polygonal meshes, our architecture leverages OpenCASCADE and build123d to synthesize exact, watertight Boundary Representation (B-Rep) 3D solids directly from natural language prompts.',
            },
            {
              q: 'What distinguishes OpenCASCADE B-Rep solids from mesh-based 3D generators?',
              a: 'Mesh generators create polygonal approximations (triangles) that suffer from non-manifold geometry, faceting, and lack exact dimensions. Our engine uses OpenCASCADE and build123d to produce analytical boundary representation (B-Rep) geometry with mathematically exact planar, cylindrical, and toroidal surfaces, fully exportable to standard CAD packages via STEP AP214.',
            },
            {
              q: 'How does the sub-140ms live slider recomputation work without LLM tokens?',
              a: 'When an initial model is synthesized, the LLM outputs a dual-output schema containing both the parameterized build123d script and a metadata array of exposed CAD parameters. When you move a slider, our backend directly re-executes the Python script with your new numeric values in a local sub-process, bypassing the AI entirely for instantaneous mechanical feedback.',
            },
            {
              q: 'What safeguards protect execution from arbitrary code execution?',
              a: 'All generated code passes through an AST (Abstract Syntax Tree) security sandbox before execution. The sandbox strictly enforces import whitelisting (build123d, math, typing only), strips all ambient environment variables (PYTHONNOUSERSITE, empty PYTHONPATH), and isolates subprocess execution with hard CPU and memory timeouts.',
            },
            {
              q: 'Can I import the generated models into Autodesk Fusion 360, SolidWorks, or 3D printers?',
              a: 'Yes. Every model generated is compiled into standard ISO 10303 STEP AP214 and watertight STL files. These open seamlessly in any professional CAD suite or 3D slicing software (Cura, PrusaSlicer, Bambu Studio) with fully intact solid bodies.',
            },
            {
              q: 'What is the complete system technology stack?',
              a: 'The frontend is built with React 18, Vite, Three.js / React Three Fiber for WebGL rendering. The backend is built with Python FastAPI, OpenCASCADE Technology 7.8, build123d parametric modeling framework, and Gemini generative reasoning.',
            },
          ].map((item, idx) => (
            <FaqItem key={idx} question={item.q} answer={item.a} />
          ))}
        </div>
      </section>

      {/* ── LUXURY WATERMARK FOOTER (.site-footer) ──────────────────── */}
      <footer style={{
        position: 'relative',
        backgroundColor: '#F6F6F0',
        borderTop: '1px solid rgba(71, 64, 64, 0.1)',
        paddingTop: '80px',
        overflow: 'hidden',
      }}>
        <div style={{
          maxWidth: '1440px',
          margin: '0 auto',
          padding: '0 clamp(16px, 4vw, 50px) 60px',
          position: 'relative',
          zIndex: 1,
        }}>
          {/* Top Footer Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '40px',
            marginBottom: '60px',
          }}>
            {/* Brand & Newsletter */}
            <div style={{ maxWidth: '320px' }}>
              <div style={{
                fontFamily: '"Newsreader", Georgia, serif',
                fontSize: '22px',
                fontWeight: '400',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                color: '#474040',
                marginBottom: '14px',
              }}>
                The CAD Atelier
              </div>
              <p style={{ fontSize: '13px', lineHeight: 1.6, color: 'rgba(71, 64, 64, 0.7)', marginBottom: '20px' }}>
                Academic minor project on generative B-Rep solid geometry, OpenCASCADE kernels, and parametric recomputation.
              </p>

              <form onSubmit={handleSubscribe} style={{ position: 'relative' }}>
                <input
                  type="email"
                  placeholder="Enter your student/academic email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 36px 10px 0',
                    border: 'none',
                    borderBottom: '1px solid rgba(71, 64, 64, 0.5)',
                    backgroundColor: 'transparent',
                    fontSize: '13px',
                    color: '#474040',
                    outline: 'none',
                    fontFamily: 'inherit',
                  }}
                />
                <button
                  type="submit"
                  style={{
                    position: 'absolute',
                    right: 0,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    color: '#474040',
                    cursor: 'pointer',
                    padding: 0,
                  }}
                >
                  <Icons.ArrowRight />
                </button>
                {subscribed && (
                  <div style={{ fontSize: '12px', color: '#489235', marginTop: '6px' }}>
                    ✓ Thank you for following the project.
                  </div>
                )}
              </form>
            </div>

            {/* Column 1: Engine */}
            <div>
              <div style={{
                fontSize: '11px',
                fontWeight: '700',
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
                color: 'rgba(71, 64, 64, 0.5)',
                marginBottom: '16px',
              }}>
                Kernel &amp; Engine
              </div>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '13px', lineHeight: 2.2 }}>
                <li><a href="#pillars" style={{ color: '#474040', textDecoration: 'none' }}>OpenCASCADE 7.8</a></li>
                <li><a href="#pillars" style={{ color: '#474040', textDecoration: 'none' }}>build123d B-Rep</a></li>
                <li><a href="#pillars" style={{ color: '#474040', textDecoration: 'none' }}>Parametric Sliders</a></li>
                <li><a href="#pillars" style={{ color: '#474040', textDecoration: 'none' }}>STEP AP214 &amp; STL</a></li>
                <li><a href="#pillars" style={{ color: '#474040', textDecoration: 'none' }}>AST Python Sandbox</a></li>
              </ul>
            </div>

            {/* Column 2: Disciplines */}
            <div>
              <div style={{
                fontSize: '11px',
                fontWeight: '700',
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
                color: 'rgba(71, 64, 64, 0.5)',
                marginBottom: '16px',
              }}>
                Case Studies
              </div>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '13px', lineHeight: 2.2 }}>
                <li><a href="#disciplines" style={{ color: '#474040', textDecoration: 'none' }}>Aerospace &amp; Turbines</a></li>
                <li><a href="#disciplines" style={{ color: '#474040', textDecoration: 'none' }}>Kinematics &amp; Gears</a></li>
                <li><a href="#disciplines" style={{ color: '#474040', textDecoration: 'none' }}>Thermal &amp; Heatsinks</a></li>
                <li><a href="#disciplines" style={{ color: '#474040', textDecoration: 'none' }}>Robotics &amp; Drones</a></li>
                <li><a href="#disciplines" style={{ color: '#474040', textDecoration: 'none' }}>Enclosures &amp; Snap-fits</a></li>
              </ul>
            </div>

            {/* Column 3: Studio */}
            <div>
              <div style={{
                fontSize: '11px',
                fontWeight: '700',
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
                color: 'rgba(71, 64, 64, 0.5)',
                marginBottom: '16px',
              }}>
                Project &amp; Links
              </div>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '13px', lineHeight: 2.2 }}>
                <li><a href="#pillars" style={{ color: '#474040', textDecoration: 'none' }}>Project Architecture</a></li>
                <li><a href="#faq" style={{ color: '#474040', textDecoration: 'none' }}>Technical FAQ</a></li>
                <li><button onClick={onEnterApp} style={{ background: 'none', border: 'none', padding: 0, color: '#474040', cursor: 'pointer', fontFamily: 'inherit', fontSize: 'inherit' }}>Launch WebGL Workbench</button></li>
                <li><a href="https://github.com/AryanAnand-ux/ai-parametric-cad-workbench" target="_blank" rel="noreferrer" style={{ color: '#474040', textDecoration: 'none' }}>GitHub Repository</a></li>
              </ul>
            </div>
          </div>

          {/* Legal Bar */}
          <div style={{
            borderTop: '1px solid rgba(71, 64, 64, 0.1)',
            paddingTop: '24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '16px',
            fontSize: '12px',
            color: 'rgba(71, 64, 64, 0.65)',
          }}>
            <div>© 2025 AI Parametric CAD Workbench · Academic Minor Project by Aryan Anand.</div>
            <div style={{ display: 'flex', gap: '20px' }}>
              <span>OpenCASCADE LGPL</span>
              <span>build123d Apache 2.0</span>
              <span>FastAPI MIT</span>
            </div>
          </div>
        </div>

        {/* Giant Watermark Text ("BY CAD ATELIER") */}
        <div style={{
          width: '100%',
          overflow: 'hidden',
          whiteSpace: 'nowrap',
          fontFamily: '"Newsreader", Georgia, serif',
          fontSize: 'clamp(72px, 11vw, 150px)',
          fontWeight: '400',
          textTransform: 'uppercase',
          color: 'rgba(71, 64, 64, 0.05)',
          textAlign: 'center',
          lineHeight: 0.9,
          userSelect: 'none',
          pointerEvents: 'none',
        }}>
          AI CAD WORKBENCH
        </div>

        {/* Bottom Craft Panoramic Banner with Direct CTA */}
        <div style={{
          position: 'relative',
          width: '100%',
          height: 'clamp(260px, 35vh, 420px)',
          backgroundImage: `url(${bottomCraftBg})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <div style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: 'rgba(71, 64, 64, 0.45)',
          }} />

          <div style={{ position: 'relative', zIndex: 2, textAlign: 'center', color: '#FFFFFF', padding: '0 20px' }}>
            <h2 style={{
              fontFamily: '"Newsreader", Georgia, serif',
              fontSize: 'clamp(32px, 4.5vw, 54px)',
              fontWeight: '400',
              margin: '0 0 16px',
            }}>
              Ready to test the parametric CAD workbench?
            </h2>
            <button
              onClick={onEnterApp}
              style={{
                backgroundColor: '#FFFDE2',
                color: '#474040',
                border: 'none',
                borderRadius: '6px',
                padding: '14px 32px',
                fontSize: '14px',
                fontWeight: '700',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 12px 28px rgba(0, 0, 0, 0.35)',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.backgroundColor = '#FFFFFF';
                e.currentTarget.style.transform = 'scale(1.03)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.backgroundColor = '#FFFDE2';
                e.currentTarget.style.transform = 'none';
              }}
            >
              <span>Launch 3D WebGL Workbench</span>
              <Icons.ArrowRight />
            </button>
          </div>
        </div>
      </footer>

      {/* ── EXPANDABLE VIDEO / 3D DEMO LIGHTBOX MODAL ──────────────── */}
      {videoModalOpen && (
        <div
          onClick={() => setVideoModalOpen(false)}
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9999,
            backgroundColor: 'rgba(71, 64, 64, 0.82)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
            animation: 'fadeIn 0.25s ease',
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              width: '100%',
              maxWidth: '900px',
              backgroundColor: '#FFFFFF',
              borderRadius: '16px',
              overflow: 'hidden',
              boxShadow: '0 24px 60px rgba(0, 0, 0, 0.4)',
              position: 'relative',
            }}
          >
            {/* Modal Header */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '18px 24px',
              borderBottom: '1px solid rgba(71, 64, 64, 0.1)',
              backgroundColor: '#F6F6F0',
            }}>
              <div>
                <span style={{
                  fontFamily: '"Newsreader", Georgia, serif',
                  fontSize: '20px',
                  color: '#474040',
                }}>
                  The CAD Atelier Session
                </span>
                <span style={{ fontSize: '12px', color: 'rgba(71, 64, 64, 0.6)', marginLeft: '12px' }}>
                  OpenCASCADE 7.8 B-Rep Engine in Action
                </span>
              </div>
              <button
                onClick={() => setVideoModalOpen(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#474040',
                  padding: '4px',
                }}
              >
                <Icons.Close />
              </button>
            </div>

            {/* Modal Media Preview */}
            <div style={{ position: 'relative', width: '100%', aspectRatio: '16/9', backgroundColor: '#000000' }}>
              <img
                src={kinematicsImg}
                alt="Horology Planetary Gear System"
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
              <div style={{
                position: 'absolute',
                inset: 0,
                backgroundColor: 'rgba(71, 64, 64, 0.3)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '16px',
                color: '#FFFDE2',
              }}>
                <button
                  onClick={onEnterApp}
                  style={{
                    backgroundColor: '#FFFDE2',
                    color: '#474040',
                    border: 'none',
                    borderRadius: '50px',
                    padding: '16px 32px',
                    fontSize: '15px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
                  }}
                >
                  <Icons.Play />
                  <span>Enter Live Interactive Workbench</span>
                </button>
                <span style={{ fontSize: '13px', opacity: 0.9 }}>
                  Real-time WebGL rendering with OrbitControls &amp; PBR Shading
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Global Embedded Styles */}
      <style>{`
        * { box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>
    </div>
  );
}

function FaqItem({ question, answer }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ borderBottom: '1px solid rgba(71, 64, 64, 0.15)' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '22px 0',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
          gap: '16px',
          fontFamily: 'inherit',
        }}
      >
        <span style={{
          fontFamily: '"Newsreader", Georgia, serif',
          fontSize: '20px',
          fontWeight: '400',
          color: '#474040',
        }}>
          {question}
        </span>
        <span style={{
          fontSize: '22px',
          color: 'rgba(71, 64, 64, 0.6)',
          transform: open ? 'rotate(45deg)' : 'none',
          transition: 'transform 0.25s ease',
          lineHeight: 1,
          flexShrink: 0,
        }}>
          +
        </span>
      </button>

      <div style={{
        maxHeight: open ? '320px' : 0,
        overflow: 'hidden',
        transition: 'max-height 0.35s ease',
      }}>
        <p style={{
          fontSize: '14px',
          lineHeight: 1.75,
          color: 'rgba(71, 64, 64, 0.75)',
          margin: '0 0 24px',
        }}>
          {answer}
        </p>
      </div>
    </div>
  );
}
