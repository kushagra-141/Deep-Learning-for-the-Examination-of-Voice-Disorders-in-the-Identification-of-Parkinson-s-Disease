export function DisclaimerBanner() {
  return (
    <div className="bg-warning text-warning-foreground px-4 py-2 text-sm font-medium text-center shadow-sm">
      <span className="flex items-center justify-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
          <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
          <path d="M12 9v4" />
          <path d="M12 17h.01" />
        </svg>
        <strong>Research Demo Only:</strong> Not a diagnostic tool. Consult a qualified medical professional for health advice.
      </span>
    </div>
  );
}
