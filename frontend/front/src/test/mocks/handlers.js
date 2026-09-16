import { http, HttpResponse } from 'msw';

export const handlers = [
    http.post('*/auth/token/', () => {
        return HttpResponse.json({ access: 'fake-access-token', refresh: 'fake-refresh-token' });
    }),
    http.get('*/auth/me/', () => {
        return HttpResponse.json({ id: 1, email: 'user@example.com', first_name: 'Test' });
    }),
];
