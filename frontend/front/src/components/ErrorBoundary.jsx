import { Component } from 'react';

class ErrorBoundary extends Component {
    state = { hasError: false };

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    componentDidCatch(error, info) {
        console.error('Uncaught render error:', error, info);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="error-boundary-fallback">
                    <p>Something went wrong. Please reload the page.</p>
                </div>
            );
        }
        return this.props.children;
    }
}

export default ErrorBoundary;
