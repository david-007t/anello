export const clerkAuthAppearance = {
  variables: {
    colorBackground: '#0d0d0d',
    colorInputBackground: 'rgba(255,255,255,0.08)',
    colorInputText: '#ffffff',
    colorText: '#ffffff',
    colorTextSecondary: '#94a3b8',
    colorPrimary: '#6366f1',
    colorDanger: '#ef4444',
    borderRadius: '12px',
    colorNeutral: '#ffffff',
  },
  elements: {
    card: {
      backgroundColor: 'rgba(255,255,255,0.05)',
      backdropFilter: 'blur(12px)',
      border: '1px solid rgba(255,255,255,0.1)',
      boxShadow: 'none',
    },
    headerTitle: {
      color: '#ffffff',
    },
    headerSubtitle: {
      color: '#94a3b8',
    },
    socialButtonsBlockButton: {
      backgroundColor: 'rgba(255,255,255,0.04)',
      border: '1px solid rgba(255,255,255,0.12)',
      color: '#ffffff',
      boxShadow: 'none',
    },
    socialButtonsBlockButtonText: {
      color: '#ffffff',
      fontWeight: '600',
    },
    dividerLine: {
      backgroundColor: 'rgba(255,255,255,0.12)',
    },
    dividerText: {
      color: '#94a3b8',
    },
    formFieldInput: {
      backgroundColor: 'rgba(255,255,255,0.08)',
      color: '#ffffff',
      border: '1px solid rgba(255,255,255,0.12)',
      boxShadow: 'none',
    },
    formButtonPrimary: {
      backgroundColor: '#6366f1',
      color: '#ffffff',
      boxShadow: 'none',
      fontWeight: '600',
    },
    footerActionLink: {
      color: '#818cf8',
    },
    footerActionText: {
      color: '#94a3b8',
    },
    identityPreviewText: {
      color: '#ffffff',
    },
    formFieldLabel: {
      color: '#e2e8f0',
    },
  },
} as const;
