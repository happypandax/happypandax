import classNames from 'classnames';
import _ from 'lodash';
import { useCallback, useState } from 'react';
import {
  RatingIconProps,
  RatingProps,
  SemanticCOLORS,
} from 'semantic-ui-react';
import { SemanticICONS } from 'semantic-ui-react/dist/commonjs/generic';

function RatingIcon({ as: ElementType = 'i', ...props }: RatingIconProps) {
  return (
    <ElementType
      {...props}
      className={classNames(
        { active: props.active, selected: props.selected },
        'icon',
        props.icon,
        props.className
      )}
      onClick={useCallback(
        (e) => {
          props.onClick?.(e, { as: ElementType, ...props });
        },
        [ElementType, props]
      )}
      onMouseEnter={useCallback(
        (e) => {
          props.onMouseEnter?.(e, { as: ElementType, ...props });
        },
        [ElementType, props]
      )}
      role="radio"
    />
  );
}

export default function Rating({
  as: ElementType = 'div',
  clearable = 'auto',
  maxRating = 1,
  rating: initialRating,
  icon,
  color,
  ...props
}: Omit<RatingProps, 'icon'> & {
  color?: SemanticCOLORS;
  icon: SemanticICONS;
}) {
  const allProps = {
    as: ElementType,
    rating: initialRating,
    clearable,
    maxRating,
    icon,
    color,
    ...props,
  };

  const [stateRating, setRating] = useState(props.defaultRating ?? 0);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isSelecting, setIsSelecting] = useState(false);

  const rating = initialRating ?? stateRating;

  const selected = isSelecting && !props.disabled && selectedIndex >= 0;

  const onClick = useCallback(
    (e, { index }) => {
      if (props.disabled) return;

      // default newRating is the clicked icon
      // allow toggling a binary rating
      // allow clearing ratings
      let newRating = index + 1;
      if (clearable === 'auto' && maxRating === 1) {
        newRating = +!rating;
      } else if (clearable === true && newRating === rating) {
        newRating = 0;
      }

      setRating(newRating);
      setIsSelecting(false);

      props.onRate?.(e, { ...allProps, rating: newRating });
    },
    [allProps, rating]
  );

  const onMouseEnter = useCallback(
    (e, { index }) => {
      if (props.disabled) return;

      setSelectedIndex(index);
      setIsSelecting(true);
    },
    [props.disabled]
  );

  return (
    <ElementType
      {...props}
      className={classNames(
        'ui rating',

        props.size,
        color,
        { active: props.active, selected, disabled: props.disabled },
        props.className
      )}
      tabIndex={props.disabled ? 0 : -1}
      onMouseLeave={useCallback(
        (...args) => {
          props.onMouseLeave?.(...args);
          if (props.disabled) return;

          setSelectedIndex(-1);
          setIsSelecting(false);
        },
        [props.onMouseLeave, props.disabled]
      )}
      role="radiogroup"
    >
      {_.times(maxRating, (i) => (
        <RatingIcon
          tabIndex={props.disabled ? -1 : 0}
          active={rating >= i + 1}
          aria-checked={rating === i + 1}
          aria-posinset={i + 1}
          aria-setsize={maxRating}
          index={i}
          icon={icon}
          key={`${rating}-${i}`}
          onClick={onClick}
          onMouseEnter={onMouseEnter}
          selected={selectedIndex >= i && isSelecting}
        />
      ))}
    </ElementType>
  );
}
