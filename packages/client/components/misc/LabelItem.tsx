import classNames from 'classnames';
import { forwardRef, ForwardRefExoticComponent } from 'react';
import { HtmlImageProps, Label, Ref } from 'semantic-ui-react';

const LabelItem_ = forwardRef<
  HTMLDivElement,
  React.ComponentProps<typeof Label> & { fluid?: boolean }
>(function LabelItem({ children, className, fluid, ...props }, ref) {
  return (
    <Ref innerRef={ref}>
      <Label
        image
        {...props}
        className={classNames(className, 'item', { fluid })}
      >
        {children}
      </Label>
    </Ref>
  );
});

function LabelItemContent({
  children,
  className,
  ...props
}: {
  children: React.ReactNode & React.HTMLAttributes<HTMLDivElement>;
  className?: string;
}) {
  return (
    <div {...props} className={classNames(className, 'content')}>
      {children}
    </div>
  );
}

function LabelItemImage({ src, alt, className, ...props }: HtmlImageProps) {
  return (
    <img
      {...props}
      className={classNames(className, 'image')}
      src={src}
      alt={alt}
    />
  );
}

interface LabelItemComponent
  extends ForwardRefExoticComponent<React.ComponentProps<typeof LabelItem_>> {
  Content: typeof LabelItemContent;
  Image: typeof LabelItemImage;
  Detail: typeof Label.Detail;
}

const LabelItem = LabelItem_ as LabelItemComponent;

LabelItem.Content = LabelItemContent;
LabelItem.Image = LabelItemImage;
LabelItem.Detail = Label.Detail;

export default LabelItem;
