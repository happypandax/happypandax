import { Segment, Form, Divider, Message, Button } from 'semantic-ui-react';
import t from '../misc/lang';

export function LoginForm() {
  return (
    <>
      <Button primary fluid color="violet">{t`Continue as Guest`}</Button>
      <Divider hidden horizontal />
      <Form error>
        <Form.Input label={t`Username`} placeholder="default"></Form.Input>
        <Form.Input label={t`Password`} type="password"></Form.Input>
        <Message error>{t`Wrong username/password combination!`}</Message>
        <Button primary floated="right">{t`Connect`}</Button>
      </Form>
    </>
  );
}

export function LoginSegment() {
  return (
    <Segment clearing>
      <div className="center-text">
        <img src="/img/hpx_logo.svg" className="hpxlogo" alt="hpxlogo" />
      </div>
      <Divider hidden horizontal />
      <LoginForm />
    </Segment>
  );
}
