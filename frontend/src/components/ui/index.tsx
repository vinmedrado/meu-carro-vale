type SurfaceProps = {
  children: React.ReactNode;
  className?: string;
  id?: string;
};

export function Surface({ children, className = '', id }: SurfaceProps) {
  return <div id={id} className={`surface mcv-surface ${className}`}>{children}</div>;
}

export function MotionSurface({ children, className = '', id }: SurfaceProps & { delay?: number }) {
  return <div id={id} className={`surface mcv-surface mcv-soft-enter ${className}`}>{children}</div>;
}

export function Button({ children, variant = 'primary', className = '', ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'ghost' }) {
  return <button className={`btn mcv-button ${variant === 'ghost' ? 'btn-ghost' : 'btn-primary'} ${className}`} {...props}>{children}</button>;
}
