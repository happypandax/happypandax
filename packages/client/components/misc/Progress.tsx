import classNames from 'classnames';
import _ from 'lodash';
import { ProgressProps } from 'semantic-ui-react';

export function Progress({
  as: ElementType = 'div',
  active,
  attached,
  className,
  color,
  disabled,
  error,
  indicating,
  inverted,
  autoSuccess,
  progress,
  children,
  content,
  precision,
  indeterminate,
  centered,
  percent,
  label,
  speed,
  total,
  value,
  size,
  success,
  warning,
  ...props
}: ProgressProps & {
  centered?: boolean;
  indeterminate?: boolean | 'filling' | 'sliding' | 'swinging' | 'pulsating';
  speed?: 'slow' | 'fast';
}) {
  const isAutoSuccess = autoSuccess && (percent >= 100 || value >= total);

  const calculatePercent = () => {
    if (!_.isUndefined(percent)) return percent;
    if (!_.isUndefined(total) && !_.isUndefined(value))
      return (parseFloat(value as string) / parseFloat(total as string)) * 100;
  };

  const getPercent = () => {
    const percent = _.clamp(calculatePercent() as number, 0, 100);

    if (
      !_.isUndefined(total) &&
      !_.isUndefined(value) &&
      progress === 'value'
    ) {
      return (parseFloat(value as string) / parseFloat(total as string)) * 100;
    }
    if (progress === 'value') return value;
    if (_.isUndefined(precision)) return percent;
    return _.round(percent, precision);
  };

  const computedPercent = getPercent() || 0;

  const computeValueText = (percent) => {
    if (progress === 'value') return value;
    if (progress === 'ratio') return `${value}/${total}`;
    return `${percent}%`;
  };

  return (
    <ElementType
      {...props}
      className={classNames(
        'ui',
        color,
        size,
        speed,
        {
          active: active || indicating,
          indeterminate: !!indeterminate,
          [indeterminate as string]: typeof indeterminate === 'string',
          disabled,
          error,
          indicating,
          inverted,
          success: success || isAutoSuccess,
        },
        'progress',
        className
      )}
      data-percent={
        !_.isUndefined(percent) || !_.isUndefined(value)
          ? computedPercent
          : undefined
      }
    >
      <div
        className="bar"
        style={
          !_.isUndefined(percent) || !_.isUndefined(value)
            ? { width: `${computedPercent}%` }
            : undefined
        }
      >
        {progress && (
          <div className={classNames('progress', { centered })}>
            {computeValueText(computedPercent)}
          </div>
        )}
      </div>
      {!label && (children || content) && (
        <div className="label">{children ?? content}%</div>
      )}
      {label && <div className="label">{label}</div>}
    </ElementType>
  );
}
