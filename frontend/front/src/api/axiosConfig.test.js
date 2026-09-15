import axiosInstance from './axiosConfig';
import {http, HttpResponse} from 'msw';
import {server} from "../test/mocks/server";


beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('access_token', 'old_access_token');
    localStorage.setItem('refresh_token', 'old_refresh_token');

});

describe('axiosInstance', () => {
    it('refresh breaks when access token is expired and refresh token also, like 7 days away  from computer', async () => {
        server.use(
            http.get('*/auth/me/', () => HttpResponse.json({}, { status: 401 })),
            http.post('*/auth/token/refresh/', () => HttpResponse.json({}, { status: 401 })),
        );

        const expiredListener = vi.fn();
        window.addEventListener('auth:expired', expiredListener);

        await expect(axiosInstance.get('/auth/me/')).rejects.toBeDefined();

        expect(expiredListener).toHaveBeenCalled();
        expect(localStorage.getItem('access_token')).toBeNull();
        expect(localStorage.getItem('refresh_token')).toBeNull();

        window.removeEventListener('auth:expired', expiredListener);
    })

    it('two requests triggered simultaneously with access token expired, first one can resolve, but second one fails because first invalidated the refresh token', async () => {
        let refreshCalls = 0;

        server.use(
            // Old token → 401 (simulates the expired access token).
            // New token (the one the refresh mock below issues) → 200.
            http.get('*/auth/me/', ({ request }) => {
                const auth = request.headers.get('Authorization');
                if (auth === 'Bearer new-access-token') {
                    return HttpResponse.json({ id: 1, email: 'user@example.com' });
                }
                return HttpResponse.json({}, { status: 401 });
            }),
            http.post('*/auth/token/refresh/', () => {
                refreshCalls += 1;
                if (refreshCalls === 1) {
                    return HttpResponse.json({ access: 'new-access-token', refresh: 'new-refresh-token' });
                }
                // never falls back to this case because our new axiosConfig deals with 2 racing requests trying to refresh the token.
                return HttpResponse.json({}, { status: 401 });
            }),
        );

        const results = await Promise.allSettled([
            axiosInstance.get('/auth/me/'),
            axiosInstance.get('/auth/me/'),
        ]);

        const fulfilled = results.filter((r) => r.status === 'fulfilled');

        expect(fulfilled).toHaveLength(2);
        expect(localStorage.getItem('access_token')).not.toBeNull();
    })

});