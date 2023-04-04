import React, { useCallback, useContext } from 'react';
import { useRecoilState } from 'recoil';
import {
  Button,
  Checkbox,
  Form,
  Header,
  Icon,
  Modal,
  Segment,
  Select,
} from 'semantic-ui-react';

import { ReaderContext } from '../../client/context';
import t from '../../client/lang';
import { ImageSize, ItemFit, ReadingDirection } from '../../shared/enums';
import { ReaderState } from '../../state';
import { ModalWithBack } from '../misc/BackSupport';

const sizeOptions = [
  { key: 'auto', text: t`Auto`, value: ItemFit.Auto },
  { key: 'contain', text: t`Contain`, value: ItemFit.Contain },
  { key: 'height', text: t`Height`, value: ItemFit.Height },
  { key: 'width', text: t`Width`, value: ItemFit.Width },
];

const scalingOptions = [
  { key: 0, text: t`Auto`, value: 0 },
  { key: ImageSize.Original, text: t`Original`, value: ImageSize.Original },
  { key: ImageSize.x2400, text: t`x2400`, value: ImageSize.x2400 },
  { key: ImageSize.x1600, text: t`x1600`, value: ImageSize.x1600 },
  { key: ImageSize.x1280, text: t`x1280`, value: ImageSize.x1280 },
  { key: ImageSize.x960, text: t`x960`, value: ImageSize.x960 },
  { key: ImageSize.x768, text: t`x768`, value: ImageSize.x768 },
];

const directionOptions = [
  {
    key: ReadingDirection.TopToBottom,
    text: t`↓ Top to Bottom`,
    value: ReadingDirection.TopToBottom,
  },
  {
    key: ReadingDirection.LeftToRight,
    text: t`→ Left to Right`,
    value: ReadingDirection.LeftToRight,
  },
];

export default function ReaderSettings({
  ...props
}: React.ComponentProps<typeof Segment>) {
  const { stateKey } = useContext(ReaderContext);

  const [fit, setFit] = useRecoilState(ReaderState.fit(stateKey));
  const [stretchFit, setStretchFit] = useRecoilState(
    ReaderState.stretchFit(stateKey)
  );
  const [autoScroll, setAutoScroll] = useRecoilState(
    ReaderState.autoScroll(stateKey)
  );
  const [autoScrollSpeed, setAutoScrollSpeed] = useRecoilState(
    ReaderState.autoScrollSpeed(stateKey)
  );
  const [autoNavigateInterval, setAutoNavigateInterval] = useRecoilState(
    ReaderState.autoNavigateInterval(stateKey)
  );
  const [autoReadNextCountdown, setAutoReadNextCountdown] = useRecoilState(
    ReaderState.autoReadNextCountdown(stateKey)
  );
  const [scaling, setScaling] = useRecoilState(ReaderState.scaling(stateKey));
  const [wheelZoom, setWheelZoom] = useRecoilState(
    ReaderState.wheelZoom(stateKey)
  );
  const [direction, setDirection] = useRecoilState(
    ReaderState.direction(stateKey)
  );
  const [blurryBg, setBlurryBg] = useRecoilState(
    ReaderState.blurryBg(stateKey)
  );

  return (
    <Segment basic size="tiny" {...props}>
      <Form size="small">
        <Form.Field
          control={Select}
          disabled
          label={t`Direction`}
          nChange={useCallback((ev, data) => {
            ev.preventDefault();
            setDirection(data.value);
          }, [])}
          value={direction}
          placeholder={t`Direction`}
          defaultValue={ReadingDirection.TopToBottom}
          options={directionOptions}
        />

        <Form.Group>
          <Form.Field
            control={Select}
            label={t`Fit`}
            placeholder={t`Fit`}
            onChange={useCallback((ev, data) => {
              ev.preventDefault();
              setFit(data.value);
            }, [])}
            value={fit}
            defaultValue={ItemFit.Auto}
            options={sizeOptions}
            width={10}
          />

          <Form.Field width={6}>
            <Checkbox
              label={t`Stretch`}
              checked={stretchFit}
              onChange={useCallback((ev, data) => {
                ev.preventDefault();
                setStretchFit(data.checked);
              }, [])}
            />
          </Form.Field>
        </Form.Group>

        <Form.Field
          control={Select}
          label={t`Scaling`}
          onChange={useCallback((ev, data) => {
            ev.preventDefault();
            setScaling(data.value);
          }, [])}
          value={scaling}
          placeholder={t`Scaling`}
          defaultValue={0}
          options={scalingOptions}
        />

        <Form.Field>
          <label>{t`Zoom with mouse wheel`}</label>
          <Checkbox
            toggle
            checked={wheelZoom}
            onChange={useCallback((ev, data) => {
              ev.preventDefault();
              setWheelZoom(data.checked);
            }, [])}
          />
        </Form.Field>

        <Form.Field>
          <label>{t`Blurry background`}</label>
          <Checkbox
            toggle
            checked={blurryBg}
            onChange={useCallback((ev, data) => {
              ev.preventDefault();
              setBlurryBg(data.checked);
            }, [])}
          />
        </Form.Field>

        <Form.Group>
          <Form.Field
            onChange={useCallback((ev, data) => {
              ev.preventDefault();
              const v = parseFloat(ev.target.value);
              setAutoScrollSpeed(Math.max(0, isNaN(v) ? 100 : v));
            }, [])}
            width={10}
            disabled={!autoScroll}
          >
            <label>{t`Auto scroll speed`}</label>
            <input value={autoScrollSpeed} type="number" min={0} />
          </Form.Field>

          <Form.Field width={6}>
            <Checkbox
              label={t`Auto scroll`}
              checked={autoScroll}
              onChange={useCallback((ev, data) => {
                ev.preventDefault();
                setAutoScroll(data.checked);
              }, [])}
            />
          </Form.Field>
        </Form.Group>
        <Form.Field
          onChange={useCallback((ev) => {
            ev.preventDefault();
            const v = parseFloat(ev.target.value);
            setAutoNavigateInterval(Math.max(0, isNaN(v) ? 15 : v));
          }, [])}
        >
          <label>{t`Auto navigate interval`}</label>
          <input value={autoNavigateInterval} type="number" min={0} />
          <span className="sub-text">{t`Seconds`}</span>
        </Form.Field>

        <Form.Field
          onChange={useCallback((ev) => {
            ev.preventDefault();
            const v = parseFloat(ev.target.value);
            setAutoReadNextCountdown(Math.max(0, isNaN(v) ? 15 : v));
          }, [])}
        >
          <label>{t`Auto read next gallery countdown`}</label>
          <input value={autoReadNextCountdown} type="number" min={0} />
          <span className="sub-text">{t`Set to 0 to disable`}</span>
        </Form.Field>
      </Form>
    </Segment>
  );
}

export function ReaderSettingsButton({
  ...props
}: React.ComponentProps<typeof Button>) {
  const { stateKey } = useContext(ReaderContext);

  return (
    <ModalWithBack
      size="mini"
      closeIcon
      trigger={<Button icon="setting" secondary basic circular {...props} />}
    >
      <Modal.Header>
        <Icon name="setting" /> {t`Reader Settings`}
      </Modal.Header>
      <Modal.Content>
        <ReaderSettings className="no-padding-segment" />
      </Modal.Content>
    </ModalWithBack>
  );
}
