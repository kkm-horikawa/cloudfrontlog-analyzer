import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

describe('Frontend Test Setup', () => {
  it('should pass this sample test', () => {
    expect(true).toBe(true);
  });

  it('should be able to render a simple element', () => {
    render(<div data-testid="test-div">Hello Vitest</div>);
    expect(screen.getByTestId('test-div')).toBeInTheDocument();
    expect(screen.getByText('Hello Vitest')).toBeInTheDocument();
  });
});
