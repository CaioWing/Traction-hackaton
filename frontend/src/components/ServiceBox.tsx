import React from 'react';
import { styled } from 'styled-components';

const ServiceContainer = styled.div`
  width: 25vw;
  padding: 5px 10px;
  box-shadow: 10px 10px 5px 0px rgba(0, 0, 0, 0.07);
  border: solid 1px gray;
  margin: 20px;
`;

const Title = styled.h1`
  font-size: 1.5vw;
  margin: 0;
  padding: 0;
  color: black;
`;

function ServiceBox({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <ServiceContainer>
      <Title>{title}</Title>
      {children}
    </ServiceContainer>
  );
}

export default ServiceBox;
