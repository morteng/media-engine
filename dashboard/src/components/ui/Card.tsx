import * as React from 'react';
import clsx from 'clsx';

export type CardVariant =
  | 'default'
  | 'elevated'
  | 'gradient'
  | 'bordered'
  | 'ghost'
  | 'interactive'
  | 'glow'; // Legacy variant for backward compatibility

export type CardPadding = 'compact' | 'default' | 'spacious' | 'none';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  padding?: CardPadding;
}

const variantStyles: Record<CardVariant, string> = {
  default: 'bg-base-200 border border-base-300 shadow-sm',
  elevated: 'bg-base-200 border border-base-300 shadow-lg hover:shadow-xl transition-shadow',
  gradient: 'bg-gradient-to-br from-base-200 to-base-300 border border-base-300',
  bordered: 'bg-base-200 border-2 border-base-300',
  ghost: 'bg-transparent border border-transparent hover:border-base-300 transition-colors',
  interactive:
    'bg-base-200 border border-base-300 shadow-sm hover:shadow-md hover:border-primary/50 hover:bg-base-200/80 transition-all cursor-pointer',
  glow: 'bg-base-200 border border-primary/30 shadow-lg shadow-primary/10',
};

const paddingStyles: Record<CardPadding, string> = {
  none: '',
  compact: 'p-3',
  default: 'p-4',
  spacious: 'p-6',
};

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', padding, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx(
        'card rounded-lg',
        variantStyles[variant],
        padding && paddingStyles[padding],
        className
      )}
      {...props}
    />
  )
);
Card.displayName = 'Card';

interface CardHeaderProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'title'> {
  title?: React.ReactNode;
  action?: React.ReactNode;
}

const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, title, action, children, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx('flex items-center justify-between p-4', className)}
      {...props}
    >
      {title ? (
        <>
          <h3 className="text-base font-semibold leading-none tracking-tight">{title}</h3>
          {action && <div className="flex-shrink-0">{action}</div>}
        </>
      ) : (
        <div className="flex flex-col space-y-1.5 flex-1">{children}</div>
      )}
    </div>
  )
);
CardHeader.displayName = 'CardHeader';

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={clsx('text-base font-semibold leading-none tracking-tight', className)}
    {...props}
  />
));
CardTitle.displayName = 'CardTitle';

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={clsx('text-sm text-base-content/60', className)}
    {...props}
  />
));
CardDescription.displayName = 'CardDescription';

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={clsx('p-4 pt-0', className)} {...props} />
));
CardContent.displayName = 'CardContent';

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={clsx('flex items-center p-4 pt-0', className)}
    {...props}
  />
));
CardFooter.displayName = 'CardFooter';

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };
