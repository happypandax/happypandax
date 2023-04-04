'use client';
import { useCallback, useEffect, useState } from 'react';
import {
  Button,
  Divider,
  Form,
  Message,
  Modal,
  Segment,
} from 'semantic-ui-react';

import t from '../client/lang';
import { MutatationType, useMutationType } from '../client/queries';
import { LOGIN_ERROR } from '../server/constants';
import { urlparse } from '../shared/utility';
import { useGlobalState, useGlobalValue } from '../state/global';
import { LabelAccordion } from './misc';

export function LoginForm({ onSuccess }: { onSuccess: () => void }) {
  const serverHost = useGlobalValue('serverHost');
  const serverPort = useGlobalValue('serverPort');
  const disableServerConnect = useGlobalValue('disableServerConnect');

  const [endpoint, setEndpoint] = useState({
    host: undefined as string,
    port: undefined as number,
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  type NextAuthErrorData = {
    url: string;
  };

  const mutation = useMutationType(MutatationType.LOGIN, {
    onSuccess: (data, variables) => {
      setEndpoint(variables.endpoint);
      localStorage.setItem(
        'server_endpoint',
        JSON.stringify(variables.endpoint)
      );
      onSuccess?.();
    },
    onError: (err) => {
      setLoading(false);

      const data = err.response?.data as unknown as NextAuthErrorData;

      if (err.response.status === 401 && data?.url) {
        console.debug(err.message, data);

        const error = urlparse(data.url).query?.error as LOGIN_ERROR;

        switch (error) {
          case LOGIN_ERROR.InvalidCredentials:
            setError(t`Wrong credentials`);
            break;
          case LOGIN_ERROR.ServerNotConnected:
            setError(
              t`Failed to connect to server` +
                ` (${endpoint.host}:${endpoint.port})`
            );
            break;
          default:
            setError(err.message + ': ' + error);
        }
      } else {
        setError(err.message + ': ' + t`Unknown error`);
      }
    },
  });

  useEffect(() => {
    if (!endpoint.host || !endpoint.port) {
      const ep = localStorage.getItem('server_endpoint');
      if (ep) {
        setEndpoint(JSON.parse(ep));
      }
    }
  }, []);

  const getEndpoint = useCallback(() => {
    if (disableServerConnect) {
      return {
        host: undefined,
        port: undefined,
      };
    }

    return {
      host: endpoint.host || serverHost || 'localhost',
      port: endpoint.port || serverPort || 7007,
    };
  }, [endpoint]);

  return (
    <>
      <Button
        fluid
        basic
        color="violet"
        onClick={(e) => {
          e.preventDefault();
          mutation.mutate({
            username: '',
            password: '',
            endpoint: getEndpoint(),
          });
        }}
      >{t`Continue as Guest`}</Button>
      <Divider hidden horizontal />
      <Form
        loading={loading}
        error={!!error}
        onSubmit={(e) => {
          e.preventDefault();
          setError('');
          setLoading(true);
          const f = new FormData(e.target as any);

          mutation.mutate({
            username: (f.get('username') as string) || 'default',
            password: f.get('password') as string,
            endpoint: getEndpoint(),
          });
        }}
      >
        {!disableServerConnect && (
          <LabelAccordion label="Server">
            <Segment basic>
              <Form.Group>
                <Form.Input
                  name="host"
                  label={t`Host`}
                  width={11}
                  value={endpoint?.host ?? ''}
                  onChange={(e, d) => {
                    setEndpoint({ ...endpoint, host: d.value });
                  }}
                  placeholder={endpoint.host ?? serverHost}
                ></Form.Input>
                <Form.Input
                  name="port"
                  label={t`Port`}
                  width={5}
                  value={endpoint?.port ?? ''}
                  onChange={(e, d) => {
                    setEndpoint({
                      ...endpoint,
                      port: d.value ? parseInt(d.value, 10) : undefined,
                    });
                  }}
                  placeholder={endpoint.port ?? serverPort}
                  type="number"
                ></Form.Input>
              </Form.Group>
            </Segment>
          </LabelAccordion>
        )}
        <Form.Input
          name="username"
          label={t`Username`}
          placeholder="default"
        ></Form.Input>
        <Form.Input
          name="password"
          label={t`Password`}
          type="password"
        ></Form.Input>
        <Message error>{error}</Message>
        <Button primary floated="right">{t`Connect`}</Button>
      </Form>
    </>
  );
}

export function LoginModal({ open }: { open?: boolean }) {
  const [loggedIn, setLoggedIn] = useGlobalState('loggedIn');

  return (
    <Modal open={open ?? !loggedIn}>
      <Segment clearing>
        <div className="center-text">
          <img src="/img/hpx_logo.svg" className="hpxlogo" alt="hpxlogo" />
        </div>
        <Divider hidden horizontal />
        <LoginForm
          onSuccess={useCallback(() => {
            setLoggedIn(true);
          }, [])}
        />
      </Segment>
    </Modal>
  );
}
