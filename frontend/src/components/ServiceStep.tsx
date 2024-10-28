import React, { useState } from 'react';
import { styled } from 'styled-components';
import { Checkbox } from '@mui/material';

const StepContainer = styled.div`
  width: 90vw;
  padding: 30px 0;
  box-shadow: 10px 10px 5px 0px rgba(0, 0, 0, 0.07);
  border: solid 1px gray;
  margin: 40px auto;
  display: flex;
`;

const StepNumber = styled.div`
  background-color: #16d6ac;
  border-radius: 50%;
  width: 60px;
  height: 60px;
  text-align: center;
  line-height: 60px;
  font-size: 50px;
  color: white;
  margin-left: 20px;
`;

const Title = styled.h1`
  margin: 0;
  padding: 0;
  color: black;
`;

const ContentDiv = styled.div`
  margin-left: 20px;
`;

const TitleDiv = styled.div`
  display: flex;
`;

const Description = styled.p`
  margin-left: 20px;
`;

const EstimatedTime = styled.p`
  margin-left: 15px;
`;

function ServiceStep({
  title,
  description,
  number,
  time,
}: {
  title: string;
  description: string;
  number: number;
  time: string;
}) {
  const [done, setDone] = useState(false);
  return (
    <StepContainer style={{ backgroundColor: done ? 'inherit' : '#80808030' }}>
      <div>
        <StepNumber style={{ backgroundColor: done ? '#16d6ac' : 'gray' }}>
          {number}
        </StepNumber>
        <div style={{ marginLeft: '20px' }}>
          <Checkbox
            onChange={() => {
              setDone(!done);
            }}
            sx={{ '& .MuiSvgIcon-root': { fontSize: 40, margin: 0 } }}
          />
        </div>
      </div>
      <ContentDiv>
        <TitleDiv>
          <Title>{title}</Title>
          <EstimatedTime>{time}</EstimatedTime>
        </TitleDiv>
        <Description>{description}</Description>
      </ContentDiv>
    </StepContainer>
  );
}

export default ServiceStep;
