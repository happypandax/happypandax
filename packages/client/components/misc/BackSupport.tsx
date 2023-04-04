import {
  forwardRef,
  useCallback,
  useImperativeHandle,
  useRef,
  useState,
} from 'react';
import { Modal, ModalProps, Ref } from 'semantic-ui-react';

import { useHijackHistory } from '../../client/hooks/ui';

export const ModalWithBack = forwardRef(
  ({ onOpen, onClose, ...props }: ModalProps, ref) => {
    const cRef = useRef<HTMLDivElement>(null);
    useImperativeHandle(ref, () => cRef.current);

    const [open, setOpen] = useState(false);

    useHijackHistory(open, () => cRef.current.click());

    return (
      <Ref innerRef={cRef}>
        <Modal
          {...props}
          onOpen={useCallback(
            (...a) => {
              setOpen(true);
              onOpen?.(...a);
            },
            [onOpen]
          )}
          onClose={useCallback(
            (...a) => {
              setOpen(false);
              onClose?.(...a);
            },
            [onClose]
          )}
        />
      </Ref>
    );
  }
);
