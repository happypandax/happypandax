'use client';
import { clientInitialize } from '../misc/initialize/client';

if (!global?.app?.initialized && process.env.NODE_ENV !== 'test') {
    await clientInitialize();
}