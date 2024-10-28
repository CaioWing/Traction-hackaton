import React from 'react';
import styled from 'styled-components';

const HeaderContainer = styled.div`
  width: 100%;
  height: 90px;
  background-color: #337dff;
`;

const Title = styled.h1`
  color: white;
  font-weight: 800;
  font-size: 5.5vh;
  margin: 0;
  margin-left: 30px;
  padding: 0;
`;

function Header() {
  return (
    <HeaderContainer>
      <Title>Gearing</Title>
    </HeaderContainer>
  );
}

export default Header;
