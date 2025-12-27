import * as React from 'react';
import clsx from 'clsx';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glow' | 'gradient';
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', ...props }, ref) => (
    <div
      ref={ref}
      className={clsx(
        'card bg-base-200 border border-base-300 rounded-lg',
        {
          'shadow-sm': variant === 'default',
          'border-primary/30 shadow-lg shadow-primary/10': variant === 'glow',
          'bg-gradient-to-br from-base-200 to-base-300': variant === 'gradient',
        },
        className
      )}
      {...props}
    />
  )
);
Card.displayName = 'Card';

// Legacy CardHeader with title/subtitle/action props for backward compatibility
interface LegacyCardHeaderProps {
  title: string;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
}

// New shadcn-style CardHeader
type NewCardHeaderProps = React.HTMLAttributes<HTMLDivElement>;

type CardHeaderProps = LegacyCardHeaderProps | NewCardHeaderProps;

function isLegacyProps(props: CardHeaderProps): props is LegacyCardHeaderProps {
  return 'title' in props && typeof props.title === 'string';
}

const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  (props, ref) => {
    if (isLegacyProps(props)) {
      const { title, subtitle, action } = props;
      return (
        <div ref={ref} className="flex items-start justify-between p-4 pb-2">
          <div className="space-y-1">
            <h3 className="text-base font-semibold leading-none tracking-tight">{title}</h3>
            {subtitle && <div className="text-sm text-base-content/60">{subtitle}</div>}
          </div>
          {action && <div className="flex-shrink-0">{action}</div>}
        </div>
      );
    }

    const { className, ...rest } = props as NewCardHeaderProps;
    return (
      <div
        ref={ref}
        className={clsx('flex flex-col space-y-1.5 p-4', className)}
        {...rest}
      />
    );
  }
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
